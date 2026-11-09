from django.conf import settings
from django.db import models


class Course(models.Model):
    uid = models.CharField(max_length=64, unique=True)
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    short_name = models.CharField(max_length=32)
    teacher = models.CharField(max_length=64, blank=True, default="")
    school = models.CharField(max_length=128, blank=True, default="")
    description = models.TextField(blank=True, default="")
    cover_url = models.CharField(max_length=500, blank=True, default="")
    category = models.CharField(max_length=64, blank=True, default="计算机科学")
    color = models.CharField(max_length=16, default="#7d302f")
    source_url = models.CharField(max_length=500, blank=True, default="")
    video_url = models.CharField(max_length=500, blank=True, default="")
    popularity = models.PositiveIntegerField(default=0)
    legacy_course_id = models.BigIntegerField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses"
        ordering = ["sort_order", "id"]
        verbose_name = "课程"
        verbose_name_plural = "课程"

    def __str__(self) -> str:
        return self.name


class KnowledgePoint(models.Model):
    DIFFICULTY_CHOICES = [
        ("入门", "入门"),
        ("进阶", "进阶"),
        ("高阶", "高阶"),
    ]

    uid = models.CharField(max_length=64, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="knowledge_points")
    name = models.CharField(max_length=160)
    chapter = models.CharField(max_length=160)
    chapter_no = models.PositiveIntegerField(default=0)
    difficulty = models.CharField(max_length=8, choices=DIFFICULTY_CHOICES, default="入门")
    description = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    legacy_node_id = models.BigIntegerField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_points"
        ordering = ["course__sort_order", "chapter_no", "sort_order", "id"]
        indexes = [
            models.Index(fields=["course", "chapter_no", "sort_order"], name="kp_course_order_idx"),
            models.Index(fields=["difficulty"], name="kp_difficulty_idx"),
            models.Index(fields=["name"], name="kp_name_idx"),
        ]
        verbose_name = "知识点"
        verbose_name_plural = "知识点"

    def __str__(self) -> str:
        return f"{self.uid} · {self.name}"


class KnowledgePointLink(models.Model):
    RELATION_CHOICES = [
        ("related", "related"),
        ("requires", "requires"),
        ("mentions", "mentions"),
    ]

    from_kp = models.ForeignKey(
        KnowledgePoint, on_delete=models.CASCADE, related_name="outgoing_links"
    )
    to_kp = models.ForeignKey(
        KnowledgePoint, on_delete=models.CASCADE, related_name="incoming_links"
    )
    relation_type = models.CharField(max_length=20, choices=RELATION_CHOICES, default="related")
    weight = models.FloatField(default=1.0)

    class Meta:
        db_table = "knowledge_point_links"
        constraints = [
            models.UniqueConstraint(
                fields=["from_kp", "to_kp", "relation_type"], name="uniq_kp_link"
            )
        ]


class GraphCategory(models.Model):
    key = models.CharField(max_length=16, unique=True)
    label = models.CharField(max_length=64)
    color = models.CharField(max_length=16)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "graph_categories"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.label


class GraphNode(models.Model):
    uid = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=160)
    category = models.ForeignKey(
        GraphCategory, to_field="key", db_column="category_key", on_delete=models.PROTECT,
        related_name="nodes"
    )
    description = models.TextField()
    difficulty = models.CharField(max_length=8, default="进阶")
    related_course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.SET_NULL, related_name="graph_nodes"
    )
    related_course_label = models.CharField(max_length=64, blank=True, default="")
    knowledge_point = models.ForeignKey(
        KnowledgePoint, null=True, blank=True, on_delete=models.SET_NULL, related_name="graph_nodes"
    )
    legacy_node_id = models.BigIntegerField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "graph_nodes"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["category"], name="graph_node_category_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class GraphEdge(models.Model):
    source = models.ForeignKey(GraphNode, on_delete=models.CASCADE, related_name="outgoing_edges")
    target = models.ForeignKey(GraphNode, on_delete=models.CASCADE, related_name="incoming_edges")
    relation = models.CharField(max_length=20, default="prerequisite")
    reason = models.TextField(blank=True, default="")
    weight = models.FloatField(default=1.0)

    class Meta:
        db_table = "graph_edges"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "target", "relation"], name="uniq_graph_edge"
            )
        ]
        indexes = [
            models.Index(fields=["target", "relation"], name="graph_edge_target_idx"),
        ]


class Document(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("processing", "processing"),
        ("ready", "ready"),
        ("failed", "failed"),
    ]

    uid = models.CharField(max_length=64, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="documents")
    knowledge_point = models.ForeignKey(
        KnowledgePoint, null=True, blank=True, on_delete=models.SET_NULL, related_name="documents"
    )
    title = models.CharField(max_length=255)
    source_name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=16, default="md")
    storage_path = models.CharField(max_length=500, blank=True, default="")
    original_filename = models.CharField(max_length=255, blank=True, default="")
    mime = models.CharField(max_length=128, blank=True, default="")
    checksum = models.CharField(max_length=64, blank=True, default="")
    byte_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    chunk_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="uploaded_documents"
    )
    legacy_course_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["-updated_at", "-id"]
        indexes = [
            models.Index(fields=["course", "status"], name="doc_course_status_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class DocumentChunk(models.Model):
    uid = models.CharField(max_length=80, unique=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chunks")
    knowledge_point = models.ForeignKey(
        KnowledgePoint, null=True, blank=True, on_delete=models.SET_NULL, related_name="chunks"
    )
    ordinal = models.IntegerField(default=0)
    title = models.CharField(max_length=200)
    content = models.TextField()
    content_hash = models.CharField(max_length=64)
    char_count = models.IntegerField(default=0)
    tokens = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    source_name = models.CharField(max_length=255)
    chapter = models.CharField(max_length=160, blank=True, default="")
    embedding = models.JSONField(null=True, blank=True)
    embedding_provider = models.CharField(max_length=32, default="local")
    embedding_model = models.CharField(max_length=64, default="blake2b-char-ngram-v1")
    embedding_dim = models.IntegerField(default=0)
    embedding_norm = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "document_chunks"
        ordering = ["document_id", "ordinal", "id"]
        indexes = [
            models.Index(fields=["document"], name="chunk_document_idx"),
            models.Index(fields=["course", "embedding_provider", "embedding_dim"], name="chunk_course_emb_idx"),
            models.Index(fields=["knowledge_point"], name="chunk_kp_idx"),
            models.Index(fields=["content_hash"], name="chunk_hash_idx"),
        ]

    def __str__(self) -> str:
        return self.uid


class LegacyImportMap(models.Model):
    entity_type = models.CharField(max_length=24)
    legacy_table = models.CharField(max_length=64)
    legacy_id = models.BigIntegerField()
    new_uid = models.CharField(max_length=80)
    checksum = models.CharField(max_length=64, blank=True, default="")
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "legacy_import_map"
        constraints = [
            models.UniqueConstraint(
                fields=["entity_type", "legacy_table", "legacy_id"], name="uniq_legacy_map"
            )
        ]
