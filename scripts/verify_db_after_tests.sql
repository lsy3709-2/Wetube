-- 실제 DB 반영 테스트 실행 후 테이블 확인
-- 실행: pytest tests/test_real_db_reflect.py tests/test_watch_real_db.py -v
-- SQLite: sqlite3 instance/wetube.db

.mode column
.headers on

SELECT '=== users ===' AS '';
SELECT id, username, email FROM users;

SELECT '=== videos ===' AS '';
SELECT id, title, user_id, views, likes FROM videos ORDER BY id;

SELECT '=== subscriptions ===' AS '';
SELECT subscriber_id, subscribed_to_id FROM subscriptions;

SELECT '=== comments ===' AS '';
SELECT id, content, user_id, video_id, parent_id, likes, dislikes, created_at, updated_at 
FROM comments ORDER BY parent_id, id, created_at;
