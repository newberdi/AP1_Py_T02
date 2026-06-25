import asyncio
import aiohttp
from pathlib import Path
from urllib.parse import urlparse
import os


def check_path(path_str):
    try:
        path = Path(path_str)
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / '.test_write_permission'
        test_file.write_text('test')
        test_file.unlink()
        return True
    except PermissionError:
        print(f"Ошибка: Нет прав доступа к пути '{path_str}'")
        return False
    except Exception as e:
        print(f"Ошибка: Некорректный путь '{path_str}' - {e}")
        return False

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])  # есть протокол и домен
    except Exception:
        return False

def generate_filename(url, used_names, unnamed_counter):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    
    if not filename or '.' not in filename:
        # нет имени
        unnamed_counter[0] += 1
        filename = f"image_{unnamed_counter[0]}.jpg"
    
    name, ext = os.path.splitext(filename)
    
    # разные url, одинаковое имя
    if filename in used_names:
        used_names[filename] += 1
        filename = f"{name}_{used_names[filename]}{ext}"
    else:
        used_names[filename] = 0
    
    return filename


async def download_image(session, url, save_path, filename, semaphore):
    async with semaphore:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    filepath = Path(save_path) / filename
                    content = await response.read()
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    return url, "Успех"
                else:
                    return url, "Ошибка"

        except Exception:
            return url, "Ошибка"


def print_summary(results):
    print("\n" + "+" + "-" * 60 + "+" + "-" * 10 + "+")
    print(f"| {'Ссылка':<58} | {'Статус':<8} |")
    print("+" + "-" * 60 + "+" + "-" * 10 + "+")
    for url, status in results:
        url_display = url if len(url) <= 58 else url[:54] + "..."
        print(f"| {url_display:<58} | {status:<8} |")
    print("+" + "-" * 60 + "+" + "-" * 10 + "+")


async def main():
    while True:
        save_path = input().strip()
        if check_path(save_path):
            break
        print("Нужно ввести другой путь.\n")
    print(f"Изображения будут сохранены в: {Path(save_path).absolute()}\n")
    
    url_to_filename = {}   # url -> готовое имя файла
    used_names = {}        # занятые имена
    unnamed_counter = [0]  # счётчик для безымянных
    
    input_urls = []        # порядок ввода всех ссылок (дубликаты+)
    
    print("Введите ссылки на изображения (пустая строка для завершения):")
    
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(5)
        tasks = []
        
        while True:
            url = (await asyncio.to_thread(input)).strip()
            if not url:
                break
            
            input_urls.append(url)

            if not is_valid_url(url):
                print(f"  [Пропущено] {url} — некорректная ссылка")
                continue
            
            if url in url_to_filename:
                print(f"  [Дубликат] {url}")
                continue
            
            filename = generate_filename(url, used_names, unnamed_counter)
            url_to_filename[url] = filename
            
            # загрузка сразу
            task = asyncio.create_task(
                download_image(session, url, save_path, filename, semaphore)
            )
            tasks.append(task)
        
        if not tasks:
            return
        
        # проверяем, остались ли загрузки
        if any(not t.done() for t in tasks):
            print("\nЗагрузка еще идет. Подождем...")
        
        download_results = await asyncio.gather(*tasks)
    
    # сравнить результаты: url -> статус
    result_map = dict(download_results)
    
    final_results = []
    for url in input_urls:
        if url in result_map:
            final_results.append((url, result_map[url]))
        elif url in url_to_filename:
            final_results.append((url, "Успех"))  # дубликат
        else:
            final_results.append((url, "Ошибка"))  # некорректная ссылка
    
    print_summary(final_results)


if __name__ == "__main__":
    asyncio.run(main())

# ./img
# https://images2.pics4learning.com/catalog/s/swamp_15.jpg
# https://bad-link-no-website-here.strange/img.png
# https://images2.pics4learning.com/catalog/p/parrot.jpg
# https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ669hacpc1JGCmf0xJAFunN3MCrQ6VdBdlng&s
# https://www.moesrealm.com/img/swamp/swamp_15.jpg