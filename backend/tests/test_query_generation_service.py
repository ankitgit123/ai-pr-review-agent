from app.services.query_generation_service import QueryGenerationService


def test_generates_css_layering_query_for_z_index_change():
    diff = """\
diff --git a/src/header.css b/src/header.css
--- a/src/header.css
+++ b/src/header.css
@@ -1,3 +1,3 @@
 .header {
-  z-index: 50;
+  z-index: 60;
 }
"""

    queries = QueryGenerationService().generate_queries(diff)

    assert len(queries) >= 2
    assert any("src/header.css" in query for query in queries)
    assert any("z-index" in query.lower() for query in queries)


def test_returns_no_queries_for_empty_diff():
    assert QueryGenerationService().generate_queries("") == []


def test_generates_fallback_query_for_unrecognized_diff():
    queries = QueryGenerationService().generate_queries(
        "Some changed content without a standard Git diff header"
    )

    assert len(queries) == 1
    assert "coding standards" in queries[0].lower()


def test_generates_security_query_for_secret_related_change():
    diff = """\
diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1 +1 @@
-API_KEY = "old"
+API_KEY = "new-secret"
"""

    queries = QueryGenerationService().generate_queries(diff)

    assert any("security standards" in query.lower() for query in queries)


def test_limits_number_of_queries():
    diff = """\
diff --git a/src/header.css b/src/header.css
--- a/src/header.css
+++ b/src/header.css
@@ -1 +1 @@
-z-index: 50;
+z-index: 60;
+token = "new-secret"
"""

    queries = QueryGenerationService().generate_queries(diff)

    assert len(queries) <= QueryGenerationService.MAX_QUERIES