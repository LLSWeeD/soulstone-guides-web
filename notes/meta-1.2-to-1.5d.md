# Soulstone Survivors — мета 1.2 → 1.5d

## Актуальная версия

На 06.10.2026 последняя подтверждённая игровая версия — **1.5d** (12.06.2026).

Цель анализа: понять, какие элементы меты версии 1.2 больше не работают в 1.5d, какие сохранились и как изменилась архитектура сильных билдов.

---

## Ключевой вывод

Мета не была полностью заменена. Большинство старых сильных архетипов сохранились, но:

1. изменились формулы scaling;
2. исчезли/переработаны отдельные конкретные синергии;
3. DoT получил полноценный scaling;
4. появились Legendary Weapons и Titan Powers;
5. Skill Type-синергии стали гораздо важнее;
6. универсальные стратегии стали менее эффективны;
7. специализация вокруг одной механики стала важнее.

Условная эволюция:

**1.2**
`Skill/Weapon → stat → damage`

→ **1.3**
`Stat → exponential scaling`

→ **1.4**
`Synergy + полноценный DoT scaling`

→ **1.5**
`Legendary Weapon + Titan Power + synergy`

→ **1.5d**
`Stack / Multiplier / специализированный DoT + Skill Type synergy + Legendary Weapon + Titan Powers`

---

# 1. Что из меты 1.2 действительно умерло

## 🔴 Quicksand + Fortitude / Max HP

Один из наиболее чистых примеров полностью сломанной старой синергии.

Старая идея:
`Max HP → Fortitude → Quicksand damage`

В 1.3 разработчики убрали у Quicksand взаимодействие с Fortitude.

Следовательно:
**старый HP → Fortitude → Quicksand билд в 1.5d больше не существует в прежнем виде.**

---

## 🔴 Linear stat scaling

В 1.3 разработчики изменили scaling ряда skills:

`linear scaling → exponential scaling`

Поэтому старые 1.2-билды, построенные на простом:
`максимизировать один stat → получать линейный damage`

нельзя переносить напрямую.

Сам принцип специализации по одному stat не умер; изменилась математика.

Современный подход:
**искать stats/skills с наиболее выгодным scaling и строить вокруг них multiplicative chain.**

---

## 🔴 Старый Elemental Flow

В старой модели DoT основным преимуществом было ускорение тиков.

В 1.5d Elemental Flow переработан:
Burn/Bleed/Poison/Doom получают полный damage сразу при наложении вместо старой модели ускорения тиков.

Следовательно, старые билды, рассчитывающие исключительно на:
`DoT duration → tick frequency → DPS`

не являются актуальной оптимальной моделью.

Современная модель:
`DoT → instant damage + scaling + multipliers`.

---

## 🔴 Старый Generalist

Старый Generalist поощрял просто наличие разных типов skills.

В 1.5d Generalist требует значительно более широкого разнообразия:
**+80% damage при ≥20 уникальных skill types.**

Поэтому старый подход:
`взять несколько разных хороших skills → получить выгоду Generalist`

больше не работает как раньше.

Современный Generalist требует специально строить очень широкий skill pool.

---

## 🔴 Старый Crit/Savage Pact scaling

Savage Pact в 1.5d ослаблен:

`40% → 30% multiplicative critical damage`

и порог HP увеличен:

`500 → 700`.

Следовательно, старые crit-билды, рассчитанные на лёгкое достижение максимального Savage Pact, стали хуже.

Однако crit как архетип НЕ умер.

---

## 🔴 Multicast как универсальный ответ

Multicast Mastery в 1.5d:

`25% → 17.5%`.

Поэтому старая стратегия:
`брать Multicast почти независимо от билда`

стала менее эффективной.

Но сам Multicast остаётся сильной механикой, особенно для:

* summons;
* weapon summons;
* projectile builds;
* некоторых Legendary Weapons;
* skills с высокой выгодой от дополнительных casts.

---

# 2. Что НЕ умерло

## 🟢 Specialization

По-прежнему одна из фундаментальных основ меты.

Современный принцип:
**выбрать одну основную damage-механику и максимально усилить именно её.**

---

## 🟢 Stack builds

По-прежнему сильный архетип.

Логика:
`Stack → scaling → multipliers → damage`

Современная версия получила больше возможностей благодаря новым skill-type synergy и Legendary Weapons.

---

## 🟢 Multiplier/Crit builds

По-прежнему сильны.

Но теперь требуется лучше подбирать:

* crit chance;
* crit potency;
* vulnerability;
* damage multipliers;
* cast frequency;
* multicast;
* Legendary Weapon;
* Titan Power.

То есть crit перестал быть настолько универсальным.

---

## 🟢 DoT

DoT не умер — он радикально усилился.

В 1.4 разработчики исправили scaling DoT.

Burn/Bleed/Poison/Doom теперь корректно получают выгоду от большого количества источников, включая различные:

* damage modifiers;
* Executioner;
* Purity;
* Searing Intensity;
* Vulnerable Exploit;
* Elite/Boss damage;
* HP-based modifiers;
* Blood Parasites;
* Ironshroom;
* Searing Ash;
* Seasoned Gladiator;
* Distant Decay;
* и др.

Современный подход:
**не смешивать все DoT бездумно, а специализироваться на одном основном ailment.**

Пример:
`Poison → Poison scaling → stacks → multipliers → execute`

или:
`Bleed → Bleed scaling → instant damage → multipliers`.

---

## 🟢 Blacksmith

Blacksmith НЕ был убит.

Уникальная механика:
**может использовать weapon skills других персонажей.**

Это всё ещё чрезвычайно сильный источник комбинаций.

Однако современная проблема — performance:
Weapon Summon spam может привести к сильному падению FPS.

Поэтому Blacksmith в современной мете:
**не слабый, а потенциально настолько сильный, что технические ограничения игры становятся ограничителем.**

---

# 3. Synchrony — важнейшее изменение

В 1.5d Synchrony значительно усилен:

`+0.7% → +1.5% damage`

и максимум:

`20% → 30%`.

Synchrony награждает повторение одинаковых Skill Types.

То есть современная игра явно противопоставляет:

### Generalist

максимальное разнообразие Skill Types

### Synchrony

повторение одинаковых Skill Types

Это две противоположные стратегии билдостроения.

---

# 4. Titan Powers

В 1.2 современной системы Titan Hunt/Titan Powers ещё не было в нынешнем виде.

Дальше появились:

* 1.3 — Faydum;
* 1.4 — Aynixle;
* 1.5 — Hecthoor + Underson.

К 1.5d Titan Powers стали полноценным слоем билдостроения.

Следовательно, прямое сравнение:
`1.2 build vs 1.5d build`

без учёта Titan Powers некорректно.

Современная структура:
`Character + Skills + Legendary Weapon + Rune/Power synergy + Titan Powers`.

---

# 5. Legendary Weapons

К 1.5 завершена большая серия Legendary Weapons.

В 1.5 добавлены последние Legendary Weapons для:

* Necromancer;
* Death Knight;
* Monkey King;
* Engineer;
* Machinist;
* Samurai.

Legendary Weapons стали одним из главных центров современных билдов.

Поэтому старый 1.2 подход:
`skill-centric`

часто превращается в современный:
`Legendary Weapon-centric`.

---

# 6. Современные основные архетипы

Условно мету 1.5d можно разделить на:

### 1. Stack

Максимизация определённого stack/debuff и его scaling.

### 2. Multiplier

Crit + critical potency + vulnerability + damage multipliers + multicast/cast frequency.

### 3. Specialized DoT

Один основной ailment + максимальное количество его синергий.

### 4. Summon

Сильные summons/weapon summons + multicast/cast frequency + соответствующие Legendary Weapons/Titan Powers.

### 5. Skill-Type synergy

Generalist:
`много уникальных skill types`

Synchrony:
`много повторяющихся skill types`

---

# 7. Условная оценка эволюции

| Архетип                 |                    1.2 |  1.5d | Изменение    |
| ----------------------- | ---------------------: | ----: | ------------ |
| Stack                   |                   ★★★★ | ★★★★★ | ↑            |
| Crit/Multiplier         |                  ★★★★★ | ★★★★½ | ↔ / слегка ↓ |
| DoT                     |                    ★★½ | ★★★★½ | ↑↑↑          |
| Summons                 |                   ★★★★ |  ★★★★ | ↔            |
| Multicast               |                  ★★★★★ |  ★★★★ | ↓            |
| Skill diversity         |                     ★★ |  ★★★★ | ↑            |
| Legendary Weapon builds |                    ★★★ | ★★★★★ | ↑↑           |
| Titan Power synergy     | отсутствует/минимальна | ★★★★★ | ↑↑↑          |

Это аналитическая оценка, не официальный tier list.

---

# 8. Практическое правило для переноса старого 1.2 билда

Нельзя просто взять старый билд и заменить устаревшие цифры.

Нужно проверить каждый слой:

### Старый слой

`Skill → Stat → Multiplier`

### Современный слой

`Skill → Skill Type → Stack/Status → Legendary Weapon → Titan Power → Rune/Power synergy → Multipliers`

Основной вопрос при реконструкции старого билда:

**«Какая современная механика выполняет ту же функцию, которую выполняла удалённая/ослабленная механика 1.2?»**

---

# 9. Самые важные конкретные изменения

**Умерли/существенно изменились:**

* Quicksand + Fortitude;
* linear stat scaling;
* старый Elemental Flow;
* старый Generalist;
* старые значения Multicast Mastery;
* старый Savage Pact/crit scaling;
* старый Chaos/debuff-universal подход.

**Сохранились:**

* specialization;
* stacking;
* crit;
* multicast;
* summons;
* DoT;
* Blacksmith;
* weapon specialization.

**Сильно выросли в значимости:**

* Legendary Weapons;
* Titan Powers;
* Skill Types;
* Synchrony;
* специализированный DoT;
* multiplicative synergy.

---

# Главный вывод

Переход 1.2 → 1.5d — это не переход:

`старые сильные персонажи → новые сильные персонажи`.

Это переход:

`сильный отдельный skill/weapon`
→
`сильная цепочка взаимодействующих механик`.

Поэтому старая мета 1.2 в основном не «слабее в цифрах», а **структурно неполна** относительно современной игры.

Наиболее перспективные старые идеи для модернизации:
**stack, crit/multiplier, DoT, summons, Blacksmith, specialization.**

Наименее пригодные для прямого переноса:
**Quicksand/Fortitude, старый Generalist, старый Elemental Flow, старый linear scaling и старые универсальные Multicast/Crit стратегии.**
