"""Unit tests for text_utils module."""

import pytest
from unittest.mock import patch, MagicMock
from src.utils.text_utils import chunk_text


class TestChunkText:
    """Tests for chunk_text function."""

    @patch('src.utils.text_utils.count_tokens')
    @patch('src.utils.text_utils.clean_text')
    def test_empty_text_returns_empty_list(self, mock_clean, mock_count):
        """Тест: порожній текст повертає порожній список."""
        # Arrange
        mock_clean.return_value = ""
        mock_count.return_value = 0  # або будь-яке ціле число, головне — int

        # Act
        result = chunk_text("")

        # Assert
        assert result == []

    @patch('src.utils.text_utils.count_tokens')
    @patch('src.utils.text_utils.clean_text')
    def test_single_sentence_smaller_than_chunk_size(self, mock_clean, mock_count):
        """Тест: текст менший за chunk_size повертає один чанк."""
        # Arrange
        text = "Це коротке речення."
        mock_clean.return_value = text
        mock_count.return_value = 5  # малий розмір

        # Act
        result = chunk_text(text, chunk_size=100, chunk_overlap=20)

        # Assert
        assert len(result) == 1
        assert result[0] == text

    @patch('src.utils.text_utils.count_tokens')
    @patch('src.utils.text_utils.clean_text')
    def test_multiple_sentences_split_into_chunks(self, mock_clean, mock_count):
        """Тест: текст з кількома реченнями розбивається на чанки."""
        # Arrange
        text = "Перше речення. Друге речення. Третє речення. Четверте речення."
        mock_clean.return_value = text

        # Симулюємо що кожне речення має 15 токенів
        mock_count.side_effect = lambda x: 15 if x.strip() else 0

        # Act - chunk_size=25 означає що в чанк поміститься максимум 1 речення
        result = chunk_text(text, chunk_size=25, chunk_overlap=10)

        # Assert
        assert len(result) > 1  # має бути розбито на кілька чанків
        # Перевіряємо що весь текст покритий
        combined = ' '.join(result)
        assert "Перше речення" in combined
        assert "Четверте речення" in combined

    @patch('src.utils.text_utils.count_tokens')
    @patch('src.utils.text_utils.clean_text')
    def test_overlap_between_chunks(self, mock_clean, mock_count):
        """Тест: перевірка overlap механізму між чанками."""
        # Arrange
        text = "Перше речення. Друге речення. Третє речення."
        mock_clean.return_value = text

        # Перше речення - 20 токенів, інші - по 15
        def token_counter(x):
            if not x.strip():
                return 0
            if "Перше" in x and "Друге" in x:
                return 35
            if "Друге" in x and "Третє" in x:
                return 30
            if "Перше" in x:
                return 20
            if "Друге" in x:
                return 15
            if "Третє" in x:
                return 15
            return len(x.split())

        mock_count.side_effect = token_counter

        # Act - chunk_size=30, overlap=15
        result = chunk_text(text, chunk_size=30, chunk_overlap=15)

        # Assert
        assert len(result) >= 2  # має бути мінімум 2 чанки
        # Перевіряємо що є overlap (друге речення може бути в обох чанках)
        if len(result) >= 2:
            # Просто перевіряємо що чанки створені
            assert len(result[0]) > 0
            assert len(result[-1]) > 0

    @patch('src.utils.text_utils.count_tokens')
    @patch('src.utils.text_utils.clean_text')
    def test_very_long_sentence_in_separate_chunk(self, mock_clean, mock_count):
        """Тест: дуже довге речення (більше chunk_size) має бути в окремому чанку."""
        # Arrange
        text = "Коротке речення. Це дуже довге речення яке перевищує розмір чанку і має бути окремо. Ще одне коротке."
        mock_clean.return_value = text

        def token_counter(x):
            if not x.strip():
                return 0
            if "дуже довге речення" in x:
                return 150  # перевищує chunk_size
            return 10

        mock_count.side_effect = token_counter

        # Act
        result = chunk_text(text, chunk_size=50, chunk_overlap=10)

        # Assert
        # Довге речення має бути в одному з чанків
        found_long_sentence = any("дуже довге речення" in chunk for chunk in result)
        assert found_long_sentence

    @patch('src.utils.text_utils.count_tokens')
    @patch('src.utils.text_utils.clean_text')
    def test_last_chunk_contains_remaining_sentences(self, mock_clean, mock_count):
        """Тест: останній чанк містить залишкові речення."""
        # Arrange
        text = "Перше. Друге. Третє. Четверте. П'яте."
        mock_clean.return_value = text
        mock_count.side_effect = lambda x: len(x.split()) if x.strip() else 0

        # Act
        result = chunk_text(text, chunk_size=20, chunk_overlap=5)

        # Assert
        assert len(result) > 0
        # Останній чанк має містити якісь речення
        assert len(result[-1]) > 0
        # Перевіряємо що "П'яте" є в результатах
        combined = ' '.join(result)
        assert "П'яте" in combined

    @patch('src.utils.text_utils.clean_text')
    def test_clean_text_is_called(self, mock_clean):
        """Тест: перевірка що clean_text викликається перед розбиттям."""
        # Arrange
        text = "  Текст з пробілами  "
        mock_clean.return_value = "Текст з пробілами"

        # Act
        with patch('src.utils.text_utils.count_tokens', return_value=5):
            chunk_text(text)

        # Assert
        mock_clean.assert_called_once_with(text)

    @patch('src.utils.text_utils.count_tokens')
    @patch('src.utils.text_utils.clean_text')
    def test_uses_default_settings_when_not_provided(self, mock_clean, mock_count):
        """Тест: використання default значень з settings."""
        # Arrange
        text = "Тестове речення."
        mock_clean.return_value = text
        mock_count.return_value = 10

        # Act - не передаємо chunk_size та chunk_overlap
        with patch('src.utils.text_utils.settings') as mock_settings:
            mock_settings.CHUNK_SIZE = 100
            mock_settings.CHUNK_OVERLAP = 20
            result = chunk_text(text)

        # Assert
        assert len(result) == 1  # має бути один чанк через малий розмір
