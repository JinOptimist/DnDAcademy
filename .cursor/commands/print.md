---
description: PDF из md в ForPrint → ForPrint/ReadyForPrint
argument-hint: [путь или ключ 0001]
---

Собери PDF для печати из документа ForPrint.

Аргумент пользователя: $ARGUMENTS

1. Прочитай этот skill: `.cursor/skills/print/SKILL.md`
2. Запусти скрипт из корня репозитория:

```
python scripts/md-to-pdf.py $ARGUMENTS
```

Можно путь (`ForPrint/NPC/0001-NPC-….md`) или ключ (`0001`).
3. PDF кладётся в `ForPrint/ReadyForPrint/` с тем же именем, расширение `.pdf`.
4. Не переписывай md. В ответе Повелителю — только путь к PDF.
