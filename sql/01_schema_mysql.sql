
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `zhiyan_zhiku` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `zhiyan_zhiku`;
DROP TABLE IF EXISTS `agent_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_runs` (
  `id` varchar(64) NOT NULL,
  `query` longtext NOT NULL,
  `top_k` smallint unsigned NOT NULL,
  `threshold` double NOT NULL,
  `retrieval_mode` varchar(12) NOT NULL,
  `status` varchar(12) NOT NULL,
  `provider` varchar(20) NOT NULL,
  `model` varchar(64) NOT NULL,
  `started_at` datetime(6) NOT NULL,
  `finished_at` datetime(6) DEFAULT NULL,
  `latency_ms` int DEFAULT NULL,
  `cited_count` int NOT NULL,
  `retrieval_snapshot` json NOT NULL,
  `config_snapshot` json NOT NULL,
  `error` longtext NOT NULL,
  `retrieval_log_id` bigint DEFAULT NULL,
  `user_id` bigint NOT NULL,
  `conversation_id` varchar(64) NOT NULL,
  `message_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `message_id` (`message_id`),
  KEY `run_conv_time_idx` (`conversation_id`,`started_at`),
  KEY `agent_runs_retrieval_log_id_bbec0cf3_fk_retrieval_logs_id` (`retrieval_log_id`),
  KEY `agent_runs_user_id_c961ab73_fk_users_id` (`user_id`),
  CONSTRAINT `agent_runs_conversation_id_8ecffb29_fk_conversations_id` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`),
  CONSTRAINT `agent_runs_message_id_95ff11c5_fk_messages_id` FOREIGN KEY (`message_id`) REFERENCES `messages` (`id`),
  CONSTRAINT `agent_runs_retrieval_log_id_bbec0cf3_fk_retrieval_logs_id` FOREIGN KEY (`retrieval_log_id`) REFERENCES `retrieval_logs` (`id`),
  CONSTRAINT `agent_runs_user_id_c961ab73_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `agent_runs_chk_1` CHECK ((`top_k` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `agent_steps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_steps` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `step_key` varchar(32) NOT NULL,
  `title` varchar(80) NOT NULL,
  `detail` longtext NOT NULL,
  `status` varchar(12) NOT NULL,
  `duration_ms` int DEFAULT NULL,
  `sort_order` int NOT NULL,
  `run_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_run_step` (`run_id`,`step_key`),
  CONSTRAINT `agent_steps_run_id_6347845a_fk_agent_runs_id` FOREIGN KEY (`run_id`) REFERENCES `agent_runs` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `agent_tool_calls`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_tool_calls` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `call_key` varchar(48) NOT NULL,
  `name` varchar(80) NOT NULL,
  `label` varchar(80) NOT NULL,
  `status` varchar(12) NOT NULL,
  `input_text` longtext NOT NULL,
  `output_text` longtext NOT NULL,
  `duration_ms` int DEFAULT NULL,
  `sort_order` int NOT NULL,
  `run_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_run_tool` (`run_id`,`call_key`),
  CONSTRAINT `agent_tool_calls_run_id_089fd010_fk_agent_runs_id` FOREIGN KEY (`run_id`) REFERENCES `agent_runs` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `citations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `citations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `index_no` int unsigned NOT NULL,
  `knowledge_point_uid` varchar(64) NOT NULL,
  `title` varchar(200) NOT NULL,
  `course_name` varchar(128) NOT NULL,
  `source_name` varchar(255) NOT NULL,
  `chapter` varchar(160) NOT NULL,
  `snippet` longtext NOT NULL,
  `score` double NOT NULL,
  `chunk_id` bigint DEFAULT NULL,
  `run_id` varchar(64) NOT NULL,
  `message_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_message_citation` (`message_id`,`index_no`),
  KEY `citations_chunk_id_38be039e_fk_document_chunks_id` (`chunk_id`),
  KEY `citations_run_id_0e079d7f_fk_agent_runs_id` (`run_id`),
  CONSTRAINT `citations_chunk_id_38be039e_fk_document_chunks_id` FOREIGN KEY (`chunk_id`) REFERENCES `document_chunks` (`id`),
  CONSTRAINT `citations_message_id_99639d74_fk_messages_id` FOREIGN KEY (`message_id`) REFERENCES `messages` (`id`),
  CONSTRAINT `citations_run_id_0e079d7f_fk_agent_runs_id` FOREIGN KEY (`run_id`) REFERENCES `agent_runs` (`id`),
  CONSTRAINT `citations_chk_1` CHECK ((`index_no` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `conversations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conversations` (
  `id` varchar(64) NOT NULL,
  `title` varchar(120) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `conv_user_updated_idx` (`user_id`,`updated_at` DESC),
  CONSTRAINT `conversations_user_id_e9bb86a0_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `courses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `uid` varchar(64) NOT NULL,
  `code` varchar(32) NOT NULL,
  `name` varchar(128) NOT NULL,
  `short_name` varchar(32) NOT NULL,
  `teacher` varchar(64) NOT NULL,
  `school` varchar(128) NOT NULL,
  `description` longtext NOT NULL,
  `cover_url` varchar(500) NOT NULL,
  `category` varchar(64) NOT NULL,
  `color` varchar(16) NOT NULL,
  `source_url` varchar(500) NOT NULL,
  `video_url` varchar(500) NOT NULL,
  `popularity` int unsigned NOT NULL,
  `sort_order` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`),
  CONSTRAINT `courses_chk_1` CHECK ((`popularity` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_users_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `document_chunks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `document_chunks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `uid` varchar(80) NOT NULL,
  `ordinal` int NOT NULL,
  `title` varchar(200) NOT NULL,
  `content` longtext NOT NULL,
  `content_hash` varchar(64) NOT NULL,
  `char_count` int NOT NULL,
  `tokens` json NOT NULL,
  `tags` json NOT NULL,
  `source_name` varchar(255) NOT NULL,
  `chapter` varchar(160) NOT NULL,
  `embedding` json DEFAULT NULL,
  `embedding_provider` varchar(32) NOT NULL,
  `embedding_model` varchar(64) NOT NULL,
  `embedding_dim` int NOT NULL,
  `embedding_norm` double NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `course_id` bigint NOT NULL,
  `document_id` bigint NOT NULL,
  `knowledge_point_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`),
  KEY `chunk_document_idx` (`document_id`),
  KEY `chunk_course_emb_idx` (`course_id`,`embedding_provider`,`embedding_dim`),
  KEY `chunk_kp_idx` (`knowledge_point_id`),
  KEY `chunk_hash_idx` (`content_hash`),
  CONSTRAINT `document_chunks_course_id_762dc970_fk_courses_id` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`),
  CONSTRAINT `document_chunks_document_id_c7107238_fk_documents_id` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`),
  CONSTRAINT `document_chunks_knowledge_point_id_7c7da3d7_fk_knowledge` FOREIGN KEY (`knowledge_point_id`) REFERENCES `knowledge_points` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `documents` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `uid` varchar(64) NOT NULL,
  `title` varchar(255) NOT NULL,
  `source_name` varchar(255) NOT NULL,
  `source_type` varchar(16) NOT NULL,
  `storage_path` varchar(500) NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `mime` varchar(128) NOT NULL,
  `checksum` varchar(64) NOT NULL,
  `byte_size` bigint NOT NULL,
  `status` varchar(16) NOT NULL,
  `chunk_count` int NOT NULL,
  `error_message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `course_id` bigint NOT NULL,
  `uploaded_by_id` bigint DEFAULT NULL,
  `knowledge_point_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`),
  KEY `documents_knowledge_point_id_10d5ff4c_fk_knowledge_points_id` (`knowledge_point_id`),
  KEY `doc_course_status_idx` (`course_id`,`status`),
  KEY `documents_uploaded_by_id_7715cd85_fk_users_id` (`uploaded_by_id`),
  CONSTRAINT `documents_course_id_29473c2d_fk_courses_id` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`),
  CONSTRAINT `documents_knowledge_point_id_10d5ff4c_fk_knowledge_points_id` FOREIGN KEY (`knowledge_point_id`) REFERENCES `knowledge_points` (`id`),
  CONSTRAINT `documents_uploaded_by_id_7715cd85_fk_users_id` FOREIGN KEY (`uploaded_by_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `graph_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `graph_categories` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `key` varchar(16) NOT NULL,
  `label` varchar(64) NOT NULL,
  `color` varchar(16) NOT NULL,
  `sort_order` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `graph_edges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `graph_edges` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `relation` varchar(20) NOT NULL,
  `reason` longtext NOT NULL,
  `weight` double NOT NULL,
  `source_id` bigint NOT NULL,
  `target_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_graph_edge` (`source_id`,`target_id`,`relation`),
  KEY `graph_edge_target_idx` (`target_id`,`relation`),
  CONSTRAINT `graph_edges_source_id_5f3424ec_fk_graph_nodes_id` FOREIGN KEY (`source_id`) REFERENCES `graph_nodes` (`id`),
  CONSTRAINT `graph_edges_target_id_6af6a79f_fk_graph_nodes_id` FOREIGN KEY (`target_id`) REFERENCES `graph_nodes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `graph_nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `graph_nodes` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `uid` varchar(64) NOT NULL,
  `name` varchar(160) NOT NULL,
  `description` longtext NOT NULL,
  `difficulty` varchar(8) NOT NULL,
  `related_course_label` varchar(64) NOT NULL,
  `sort_order` int NOT NULL,
  `category_key` varchar(16) NOT NULL,
  `related_course_id` bigint DEFAULT NULL,
  `knowledge_point_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`),
  KEY `graph_node_category_idx` (`category_key`),
  KEY `graph_nodes_related_course_id_94c529d5_fk_courses_id` (`related_course_id`),
  KEY `graph_nodes_knowledge_point_id_caa88296_fk_knowledge_points_id` (`knowledge_point_id`),
  CONSTRAINT `graph_nodes_category_key_ef62d316_fk_graph_categories_key` FOREIGN KEY (`category_key`) REFERENCES `graph_categories` (`key`),
  CONSTRAINT `graph_nodes_knowledge_point_id_caa88296_fk_knowledge_points_id` FOREIGN KEY (`knowledge_point_id`) REFERENCES `knowledge_points` (`id`),
  CONSTRAINT `graph_nodes_related_course_id_94c529d5_fk_courses_id` FOREIGN KEY (`related_course_id`) REFERENCES `courses` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `knowledge_point_links`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `knowledge_point_links` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `relation_type` varchar(20) NOT NULL,
  `weight` double NOT NULL,
  `from_kp_id` bigint NOT NULL,
  `to_kp_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_kp_link` (`from_kp_id`,`to_kp_id`,`relation_type`),
  KEY `knowledge_point_links_to_kp_id_fdf6f349_fk_knowledge_points_id` (`to_kp_id`),
  CONSTRAINT `knowledge_point_links_from_kp_id_d5c3b5e9_fk_knowledge_points_id` FOREIGN KEY (`from_kp_id`) REFERENCES `knowledge_points` (`id`),
  CONSTRAINT `knowledge_point_links_to_kp_id_fdf6f349_fk_knowledge_points_id` FOREIGN KEY (`to_kp_id`) REFERENCES `knowledge_points` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `knowledge_points`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `knowledge_points` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `uid` varchar(64) NOT NULL,
  `name` varchar(160) NOT NULL,
  `chapter` varchar(160) NOT NULL,
  `chapter_no` int unsigned NOT NULL,
  `difficulty` varchar(8) NOT NULL,
  `description` longtext NOT NULL,
  `tags` json NOT NULL,
  `sort_order` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `course_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`),
  KEY `kp_course_order_idx` (`course_id`,`chapter_no`,`sort_order`),
  KEY `kp_difficulty_idx` (`difficulty`),
  KEY `kp_name_idx` (`name`),
  CONSTRAINT `knowledge_points_course_id_4a87a935_fk_courses_id` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`),
  CONSTRAINT `knowledge_points_chk_1` CHECK ((`chapter_no` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `id` varchar(64) NOT NULL,
  `role` varchar(12) NOT NULL,
  `content` longtext NOT NULL,
  `status` varchar(12) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `latency_ms` int DEFAULT NULL,
  `stopped` tinyint(1) NOT NULL,
  `error` longtext NOT NULL,
  `conversation_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `msg_conv_time_idx` (`conversation_id`,`created_at`),
  CONSTRAINT `messages_conversation_id_5ef638db_fk_conversations_id` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `rag_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rag_settings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `top_k` smallint unsigned NOT NULL,
  `threshold` double NOT NULL,
  `retrieval_mode` varchar(12) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `rag_settings_user_id_096626b4_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `rag_settings_chk_1` CHECK ((`top_k` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `retrieval_log_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `retrieval_log_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rank` int unsigned NOT NULL,
  `dense_score` double NOT NULL,
  `lexical_score` double NOT NULL,
  `final_score` double NOT NULL,
  `chunk_uid` varchar(80) NOT NULL,
  `snapshot` json NOT NULL,
  `chunk_id` bigint DEFAULT NULL,
  `log_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_retrieval_log_rank` (`log_id`,`rank`),
  KEY `retrieval_log_items_chunk_id_a6a0122d_fk_document_chunks_id` (`chunk_id`),
  CONSTRAINT `retrieval_log_items_chunk_id_a6a0122d_fk_document_chunks_id` FOREIGN KEY (`chunk_id`) REFERENCES `document_chunks` (`id`),
  CONSTRAINT `retrieval_log_items_log_id_93a5b7e9_fk_retrieval_logs_id` FOREIGN KEY (`log_id`) REFERENCES `retrieval_logs` (`id`),
  CONSTRAINT `retrieval_log_items_chk_1` CHECK ((`rank` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `retrieval_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `retrieval_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `source` varchar(16) NOT NULL,
  `conversation_uid` varchar(64) NOT NULL,
  `message_uid` varchar(64) NOT NULL,
  `query` longtext NOT NULL,
  `retrieval_mode` varchar(12) NOT NULL,
  `top_k` smallint unsigned NOT NULL,
  `threshold` double NOT NULL,
  `candidate_count` int NOT NULL,
  `result_count` int NOT NULL,
  `embedding_ms` int NOT NULL,
  `search_ms` int NOT NULL,
  `rerank_ms` int NOT NULL,
  `total_ms` int NOT NULL,
  `embedding_provider` varchar(32) NOT NULL,
  `embedding_dim` int NOT NULL,
  `config_snapshot` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `rlog_user_time_idx` (`user_id`,`created_at` DESC),
  KEY `rlog_time_idx` (`created_at`),
  CONSTRAINT `retrieval_logs_user_id_85bb4eb6_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `retrieval_logs_chk_1` CHECK ((`top_k` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `display_name` varchar(100) NOT NULL,
  `role` varchar(120) NOT NULL,
  `avatar_text` varchar(8) NOT NULL,
  `major` varchar(120) NOT NULL,
  `grade` varchar(40) NOT NULL,
  `bio` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `users_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_groups_user_id_group_id_fc7788e8_uniq` (`user_id`,`group_id`),
  KEY `users_groups_group_id_2f3517aa_fk_auth_group_id` (`group_id`),
  CONSTRAINT `users_groups_group_id_2f3517aa_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `users_groups_user_id_f500bee5_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `users_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_user_permissions_user_id_permission_id_3b86cbdf_uniq` (`user_id`,`permission_id`),
  KEY `users_user_permissio_permission_id_6d08dcd2_fk_auth_perm` (`permission_id`),
  CONSTRAINT `users_user_permissio_permission_id_6d08dcd2_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `users_user_permissions_user_id_92473840_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

