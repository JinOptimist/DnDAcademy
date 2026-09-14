---
name: print
description: Converts a ForPrint markdown file to a print PDF in ForPrint/ReadyForPrint. Use when the user invokes /print, asks to print a ForPrint document, or to make a PDF from an md in ForPrint.
disable-model-invocation: true
---

# Print ForPrint → PDF

## Когда

Пользователь вызывает `/print` и указывает md из `ForPrint/` (путь или ключ `0001`).

## Что сделать

Из корня репозитория:

```
python scripts/md-to-pdf.py <источник>
```

`<источник>` — путь к `.md` или четырёхзначный ключ.

Скрипт сам кладёт PDF в `ForPrint/ReadyForPrint/<имя файла>.pdf`.

## Правила

- Только файлы внутри `ForPrint/`.
- Md не менять.
- Не ставить pandoc и прочие зависимости: скрипт использует Edge.
- Ответ Повелителю: путь к готовому PDF. Если скрипт упал — коротко ошибка, без обходных путей в обход скрипта.
