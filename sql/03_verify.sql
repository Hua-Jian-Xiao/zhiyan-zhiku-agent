-- 智研知库种子数据与索引完整性检查
USE `zhiyan_zhiku`;

SELECT 'courses' AS entity, COUNT(*) AS total FROM courses
UNION ALL SELECT 'knowledge_points', COUNT(*) FROM knowledge_points
UNION ALL SELECT 'knowledge_edges', COUNT(*) FROM graph_edges
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'document_chunks', COUNT(*) FROM document_chunks
UNION ALL SELECT 'graph_nodes', COUNT(*) FROM graph_nodes
UNION ALL SELECT 'graph_edges', COUNT(*) FROM graph_edges;

SELECT course_id, COUNT(*) AS knowledge_points
FROM knowledge_points
GROUP BY course_id
ORDER BY course_id;

SELECT COUNT(*) AS chunks_without_embedding
FROM document_chunks
WHERE embedding IS NULL OR embedding_dim = 0;

SELECT COUNT(*) AS conversations
FROM conversations;

SELECT COUNT(*) AS agent_runs
FROM agent_runs;

SELECT COUNT(*) AS retrieval_logs
FROM retrieval_logs;
