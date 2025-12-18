"""Unit tests for CrawlerService.extract_metadata method."""

import pytest
from src.services.crawler_service import CrawlerService


class TestExtractMetadata:
    """Tests for CrawlerService.extract_metadata method."""

    @pytest.fixture
    def crawler_service(self):
        """Створити екземпляр CrawlerService."""
        return CrawlerService()

    def test_extracts_title_from_html(self, crawler_service):
        """Тест: витягування title з HTML."""
        # Arrange
        html = """
        <html>
            <head>
                <title>Положення про академічну доброчесність</title>
            </head>
            <body>
                <p>Текст документа</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'title' in result
        assert result['title'] == 'Положення про академічну доброчесність'

    def test_extracts_document_number_with_space(self, crawler_service):
        """Тест: витягування номера документа з пробілом "№ 123"."""
        # Arrange
        html = """
        <html>
            <body>
                <p>Наказ № 2133 про затвердження положення</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'document_number' in result
        assert result['document_number'] == '2133'

    def test_extracts_document_number_without_space(self, crawler_service):
        """Тест: витягування номера документа без пробілу "№123"."""
        # Arrange
        html = """
        <html>
            <body>
                <p>Наказ №456 від 01.01.2024</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'document_number' in result
        assert result['document_number'] == '456'

    def test_extracts_date_in_correct_format(self, crawler_service):
        """Тест: витягування дати у форматі DD.MM.YYYY."""
        # Arrange
        html = """
        <html>
            <body>
                <p>Документ затверджено 15.03.2024 року</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'date' in result
        assert result['date'] == '15.03.2024'

    def test_extracts_all_metadata_when_present(self, crawler_service):
        """Тест: витягування всіх метаданих коли вони присутні."""
        # Arrange
        html = """
        <html>
            <head>
                <title>Положення про студентське самоврядування</title>
            </head>
            <body>
                <h1>Наказ № 789</h1>
                <p>Затверджено 20.05.2024</p>
                <p>Текст положення...</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'title' in result
        assert result['title'] == 'Положення про студентське самоврядування'
        assert 'document_number' in result
        assert result['document_number'] == '789'
        assert 'date' in result
        assert result['date'] == '20.05.2024'

    def test_no_title_when_tag_missing(self, crawler_service):
        """Тест: title відсутній в результаті коли немає тегу."""
        # Arrange
        html = """
        <html>
            <body>
                <p>Текст без заголовку</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'title' not in result

    def test_no_document_number_when_pattern_not_found(self, crawler_service):
        """Тест: document_number відсутній коли патерн не знайдено."""
        # Arrange
        html = """
        <html>
            <body>
                <p>Текст без номера документа</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'document_number' not in result

    def test_no_date_when_pattern_not_found(self, crawler_service):
        """Тест: date відсутня коли патерн не знайдено."""
        # Arrange
        html = """
        <html>
            <body>
                <p>Текст без дати</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'date' not in result

    def test_empty_html_returns_empty_dict(self, crawler_service):
        """Тест: порожній HTML повертає порожній словник (або словник без ключів)."""
        # Arrange
        html = ""

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert isinstance(result, dict)
        # Перевіряємо що основні ключі відсутні
        assert 'title' not in result
        assert 'document_number' not in result
        assert 'date' not in result

    def test_handles_malformed_html(self, crawler_service):
        """Тест: обробка некоректного HTML."""
        # Arrange
        html = "<html><body><p>Незакритий тег<body>"

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        # BeautifulSoup має обробити навіть некоректний HTML
        assert isinstance(result, dict)

    def test_finds_first_occurrence_of_document_number(self, crawler_service):
        """Тест: знаходження першого входження номера документа."""
        # Arrange
        html = """
        <html>
            <body>
                <p>Наказ № 111 замінює наказ № 222</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'document_number' in result
        # Має знайти перший номер
        assert result['document_number'] == '111'

    def test_finds_first_occurrence_of_date(self, crawler_service):
        """Тест: знаходження першого входження дати."""
        # Arrange
        html = """
        <html>
            <body>
                <p>Створено 10.01.2024, оновлено 20.02.2024</p>
            </body>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'date' in result
        # Має знайти першу дату
        assert result['date'] == '10.01.2024'

    def test_title_is_stripped_of_whitespace(self, crawler_service):
        """Тест: title очищено від зайвих пробілів."""
        # Arrange
        html = """
        <html>
            <head>
                <title>
                    Положення з пробілами
                </title>
            </head>
        </html>
        """

        # Act
        result = crawler_service.extract_metadata(html)

        # Assert
        assert 'title' in result
        assert result['title'] == 'Положення з пробілами'
        # Перевіряємо що немає зайвих пробілів на початку/кінці
        assert not result['title'].startswith(' ')
        assert not result['title'].endswith(' ')
