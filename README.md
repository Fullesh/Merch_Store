## Запуск проекта с использованием Docker

### Шаги по запуску

1. **Клонируйте репозиторий**
    ```bash
    git clone https://github.com/Fullesh/Merch_Store.git
    cd Merch_Store
    ```

2. **Переименуйте пример файла окружения с .env_example в .env и отредактируйте его** \
       *P/S.: СУБД PostgreSQL*



4. **Постройте и запустите контейнеры Docker**
    ```
    docker-compose up -d --build
    ```

5. **Создание суперпользователя**
   ```
   docker-compose exec app python manage.py csu
   ```
   
    *Дополнительно* \
    Данные для входа под аккаунтом администратора: \
    *Логин: admin@service.py* \
    *Пароль: 1* 

### Доступ к приложению
- Приложение будет доступно по адресу: [http://localhost:8080](http://localhost:8080)
- Админ панель Django: [http://localhost:8080/admin](http://localhost:8080/admin)

### Остановка контейнеров
Для остановки контейнеров используйте следующую команду:

```
docker-compose down
```

