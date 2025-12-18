"""Unit tests for VectorRetriever.search_by_embedding method."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from src.rag.retriever import VectorRetriever
from src.models.database import Chunk


class TestSearchByEmbedding:
    """Tests for VectorRetriever.search_by_embedding method."""

    @pytest.fixture
    def mock_db(self):
        """Створити mock об'єкт бази даних."""
        return MagicMock()

    @pytest.fixture
    def mock_embedding_service(self):
        """Створити mock embedding service."""
        return MagicMock()

    @pytest.fixture
    def retriever(self, mock_db):
        """Створити VectorRetriever з mock DB."""
        with patch('src.rag.retriever.get_embedding_service'):
            return VectorRetriever(mock_db)

    def test_uses_default_settings_when_none(self, retriever, mock_db):
        """Тест: використання default значень з settings коли параметри None."""
        # Arrange
        query_embedding = [0.1, 0.2, 0.3]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        with patch('src.rag.retriever.settings') as mock_settings:
            mock_settings.TOP_K = 10
            mock_settings.SIMILARITY_THRESHOLD = 0.7

            # Act
            retriever.search_by_embedding(
                query_embedding,
                top_k=None,
                similarity_threshold=None
            )

            # Assert
            call_args = mock_db.execute.call_args
            params = call_args[0][1]
            assert params['top_k'] == 10
            assert params['threshold'] == 0.7

    def test_converts_embedding_to_pgvector_format(self, retriever, mock_db):
        """Тест: конвертація embedding у формат pgvector."""
        # Arrange
        query_embedding = [0.1, 0.2, 0.3]
        expected_format = '[0.1,0.2,0.3]'
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        retriever.search_by_embedding(query_embedding, top_k=5, similarity_threshold=0.5)

        # Assert
        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params['query_embedding'] == expected_format

    def test_passes_correct_parameters_to_sql(self, retriever, mock_db):
        """Тест: передача коректних параметрів у SQL запит."""
        # Arrange
        query_embedding = [0.5, 0.6, 0.7]
        top_k = 3
        threshold = 0.8
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        retriever.search_by_embedding(query_embedding, top_k=top_k, similarity_threshold=threshold)

        # Assert
        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params['query_embedding'] == '[0.5,0.6,0.7]'
        assert params['top_k'] == top_k
        assert params['threshold'] == threshold

    def test_returns_empty_list_when_no_results(self, retriever, mock_db):
        """Тест: повернення порожнього списку коли нічого не знайдено."""
        # Arrange
        query_embedding = [0.1, 0.2, 0.3]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []  # немає результатів
        mock_db.execute.return_value = mock_result

        # Act
        result = retriever.search_by_embedding(query_embedding, top_k=5, similarity_threshold=0.5)

        # Assert
        assert result == []

    def test_returns_chunks_for_found_results(self, retriever, mock_db):
        """Тест: повернення списку Chunk об'єктів для знайдених результатів."""
        # Arrange
        query_embedding = [0.1, 0.2, 0.3]

        # Mock результатів SQL запиту
        mock_row1 = (1, 10, "content1", 0, None, {}, "2024-01-01", 0.85)
        mock_row2 = (2, 10, "content2", 1, None, {}, "2024-01-01", 0.75)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_db.execute.return_value = mock_result

        # Mock Chunk об'єктів
        mock_chunk1 = MagicMock(spec=Chunk)
        mock_chunk1.id = 1
        mock_chunk2 = MagicMock(spec=Chunk)
        mock_chunk2.id = 2

        # Mock query().filter().first()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.side_effect = [mock_chunk1, mock_chunk2]

        # Act
        result = retriever.search_by_embedding(query_embedding, top_k=5, similarity_threshold=0.5)

        # Assert
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_filters_by_similarity_threshold(self, retriever, mock_db):
        """Тест: фільтрація результатів за similarity_threshold."""
        # Arrange
        query_embedding = [0.1, 0.2, 0.3]
        threshold = 0.8

        # SQL запит має фільтрувати по threshold
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        retriever.search_by_embedding(query_embedding, top_k=10, similarity_threshold=threshold)

        # Assert
        call_args = mock_db.execute.call_args
        sql_query = call_args[0][0]
        params = call_args[0][1]

        # Перевіряємо що в SQL є умова з threshold
        assert 'threshold' in params
        assert params['threshold'] == threshold
        # SQL має містити умову фільтрації
        assert '>=' in str(sql_query)

    def test_limits_results_by_top_k(self, retriever, mock_db):
        """Тест: обмеження кількості результатів до top_k."""
        # Arrange
        query_embedding = [0.1, 0.2, 0.3]
        top_k = 3

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        retriever.search_by_embedding(query_embedding, top_k=top_k, similarity_threshold=0.5)

        # Assert
        call_args = mock_db.execute.call_args
        sql_query = call_args[0][0]
        params = call_args[0][1]

        # Перевіряємо що передано top_k
        assert 'top_k' in params
        assert params['top_k'] == top_k
        # SQL має містити LIMIT
        assert 'LIMIT' in str(sql_query)

    def test_handles_chunks_with_null_values(self, retriever, mock_db):
        """Тест: обробка випадку коли chunk не знайдено в БД."""
        # Arrange
        query_embedding = [0.1, 0.2, 0.3]

        # Mock результат з одним ID
        mock_row = (999, 10, "content", 0, None, {}, "2024-01-01", 0.85)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = mock_result

        # Mock query().filter().first() повертає None (chunk не знайдено)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        # Act
        result = retriever.search_by_embedding(query_embedding, top_k=5, similarity_threshold=0.5)

        # Assert
        assert result == []  # якщо chunk не знайдено, не додаємо його

    def test_sql_uses_cosine_distance_operator(self, retriever, mock_db):
        """Тест: SQL запит використовує оператор cosine distance (<=>)."""
        # Arrange
        query_embedding = [0.1, 0.2, 0.3]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        retriever.search_by_embedding(query_embedding, top_k=5, similarity_threshold=0.5)

        # Assert
        call_args = mock_db.execute.call_args
        sql_query = str(call_args[0][0])

        # Перевіряємо що SQL містить оператор <=>
        assert '<=>' in sql_query
