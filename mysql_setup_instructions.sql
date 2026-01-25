
Please execute the following SQL commands in your MySQL client to set up the database:

```sql
CREATE DATABASE personal_dash CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'personaldash'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON personal_dash.* TO 'personaldash'@'localhost';
FLUSH PRIVILEGES;
```

**IMPORTANT:** Remember to replace `'your_secure_password'` with a strong, secure password of your choice.
