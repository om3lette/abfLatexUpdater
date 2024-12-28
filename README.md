## Функционал
- [x] Получение данных из .spec и .yaml/.yml файла с хэшами
- [x] Получение обновленных данных о пакете с [ctan.org](https://ctan.org/)
- [x] Получение данных о имеющихся в зеркале файлах.
- [x] Принудительное и автоматическое обновление локальных данных (mirror_cache.json)
- [x] Скачивание файлов с [зеркала](https://mirror.truenetwork.ru/CTAN/systems/texlive/tlnet/archive)
- [x] Загрузка файлов на [filestore](https://file-store.rosalinux.ru/)
- [x] Обновление хешей в abf.yaml и версии/эпохи/релиза в .spec
- [ ] Поддержка perl макросов в .spec
- [ ] Проверка файловой структуры в %files
- [x] Пуш изменений в удаленный репозиторий
- [ ] Запрос на сборку пакета на [abf.io](https://abf.io/)
## Как запустить
Установите зависимости
```bash
pip install -r -requirements.txt
```
Linux
```bash
python3 -m src.main
```
Windows
```bash
python -m src.main
```
## Как собрать в .exe
Требуется установить pyinstaller
```bash
pyinstaller --onefile --paths=./.venv/Lib/site-packages ./cli.py
```
## Путь к скачанным файлам и репозиториям
- Данные хранятся в ```./rpm_package_upgrade_tmp``` после запуска программы через консоль или .exe.
- Файлы каждого пакете находятся в ```./rpm_package_upgrade_tmp/<название_пакета>```
- Все скачанные с [зеркала](https://mirror.truenetwork.ru/CTAN/systems/texlive/tlnet/archive) файлы можно найти в ```./rpm_package_upgrade_tmp/<название_пакета>/data```\
Список файлов, доступных на [зеркале](https://mirror.truenetwork.ru/CTAN/systems/texlive/tlnet/archive) хранится в ```./rpm_package_upgrade_tmp/mirror_cache.json```.
Создается при первом запуске программы для ускорения дальнейшей работы.
