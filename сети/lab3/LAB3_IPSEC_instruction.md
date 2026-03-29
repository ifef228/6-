# Лабораторная работа №3: IPsec VPN «сеть — сеть» (Cisco ASA 5505)

**Дисциплина:** Сетевые технологии в АСОИУ  
**Подстановка:** группа **67**, вариант **19** (ниже все адреса уже посчитаны под эти номера).

---

## 1. Цель работы

Настроить **site-to-site IPsec VPN** между корпоративной площадкой и филиалом через интернет, обеспечить прохождение заданного трафика через туннель, настроить **динамическую маршрутизацию** между участками (по сценарию стенда), проверить туннель командами `show`. Дополнительно: **веб-сервер** и **DNS** по требованиям РИП, **имена устройств** с номером варианта.

---

## 2. Краткая теория

### 2.1. IPsec «сеть — сеть»

Трафик между подсетями шифруется **ESP** в **туннельном** режиме. Сначала по **IKEv1** согласуется защищённый канал управления (**ISAKMP SA**), затем — параметры для данных (**IPsec SA**). Аутентификация сторон — **pre-shared key (PSK)**.

### 2.2. Требования по криптографии (как в методичке)

- Шифрование **ESP: AES-256** — в конфиге задаётся связка `esp-aes` + политика IKE `encr aes`; в выводе `show crypto ipsec sa` должно быть `esp-aes 256`.
- «**AH: SHA**» в учебных схемах обычно реализуется как **целостность ESP** через **HMAC-SHA** (`esp-sha-hmac`), а не отдельный протокол AH.

Пример transform-set (как в методичке):

```text
crypto ipsec ikev1 transform-set L2L esp-aes esp-sha-hmac
```

### 2.3. ASA: уровни безопасности и ACL

Интерфейс **`outside`** имеет низкий **security-level**, **`inside`** — высокий. Трафик с низкого на высокий по умолчанию **запрещён**, пока не разрешён ACL. Список **`ENTERPRISE_PRIVATE-TRAFFIC`** с `access-group ... out interface inside` нужен, чтобы **явно разрешить** нужные потоки во внутреннюю сеть (в т.ч. после расшифровки VPN), иначе ASA может **блокировать** трафик на `inside`, хотя IPsec SA уже подняты.

### 2.4. Crypto map и «interesting traffic»

В `crypto map ... match address <ACL>` задаётся **только тот трафик**, который должен уйти в IPsec. Совпадение **object network**, масок и направлений на двух концах должно быть **согласовано**. **`set peer`** — публичный адрес **другого** ASA на `outside`.

---

## 3. Адресация для группы 67 и варианта 19

Используется соглашение: **второй октет = 67 (группа)**, **третий октет = 19 (вариант)** там, где в методичке указано `172.X.Y...`, `195.X.Y...`, `134.X.Y...`.

### 3.1. Корпоративная сеть (по формулам методички)

| Зона | Подсеть |
|------|---------|
| Корпоративная сеть (целиком) | `172.67.0.0/17` |
| DC | `172.67.0.0/18` |
| Пользователи (`Y+64` → 19+64) | `172.67.83.0/20` |
| DMZ (`Y+96` → 19+96) | `172.67.115.0/21` |
| Сетевые устройства (`Y+52` → 19+52) | `172.67.71.0/23` |
| P2P L3 (`Y+54` → 19+54) | `172.67.73.0/24` |

Пояснение: для маски `/17` сеть с якорем `172.67.19.0/17` совпадает с **`172.67.0.0/17`** (узел `172.67.19.x` лежит в этой сети).

### 3.2. Филиалы

| Филиал | Подсеть |
|--------|---------|
| Филиал 1 | `195.67.19.0/24` |
| Филиал 2 (`Y+50` → 19+50) | `195.67.69.0/24` |

### 3.3. Публичные «корпоративные» адреса (ASA и др.)

Подсеть: **`134.67.19.16/28`**

- Диапазон используемых адресов (типично): `134.67.19.17` … `134.67.19.30` (уточните у преподавателя, какой адрес — сеть/broadcast в вашем эмуляторе).

Ниже в конфигах зафиксированы пары как в учебном примере методички:

- **Головной ASA (корпоратив):** `134.67.19.17/28`
- **ASA филиала:** `134.67.19.18/28`

### 3.4. Внутренние сети для объектов crypto (по аналогии с примером методички)

Для совпадения с логикой примера (CAMPUS / BRANCH / BRANCH01):

| Object | Назначение | Подсеть в варианте 19 |
|--------|------------|------------------------|
| `CAMPUS_NETWORK` | «Кампус» (первая половина /17) | `172.67.0.0/17` → маска `255.255.128.0` |
| `BRANCH_NETWORK` | Агрегат «веток» (как в примере) | `172.67.128.0/17` → маска `255.255.128.0` |
| `BRANCH01_NETWORK` | Внутренняя сеть за филиальным ASA | `172.67.129.0/24` |
| `PRIVATE_NETWORK` | Как в методичке (не менять без указания) | `176.16.0.0/16` |

Линк **головной ASA ↔ внутренний маршрутизатор** (как в примере `/30`):

- ASA `inside`: **`172.67.254.254/30`**
- Сосед (внутренний L3): **`172.67.254.253/30`**

**Филиал `inside`:** **`172.67.129.1/24`** (шлюз для `172.67.129.0/24`).

### 3.5. Предварительный общий ключ и имена

- **PSK (IKE):** `fyodorov67` (фамилия + индекс группы **без пробела**); на обоих ASA должен быть **одинаковый** ключ.
- **Имена устройств:** включайте вариант **19**, например: `DSL Modem_19_1`, `ASA-CAMPUS-VPN_19`, `ASA-BRANCH01_19`.
- **DNS A-запись:** `www.fyodorov.iu5` → IP веб-сервера в вашей DMZ/серверном сегменте (например, из `172.67.115.0/21`).

---

## 4. Конфигурация: головной ASA (корпоративная сеть)

PSK в конфиге ниже: **fyodorov67**. При необходимости скорректируйте под Packet Tracer/стенд (имена интерфейсов, доп. NAT).

```text
hostname ASA-CAMPUS-VPN_19
!
interface Vlan1
 nameif inside
 security-level 100
 ip address 172.67.254.254 255.255.255.252
!
interface Vlan2
 nameif outside
 security-level 0
 ip address 134.67.19.17 255.255.255.240
!
object network BRANCH01_NETWORK
 subnet 172.67.129.0 255.255.255.0
object network BRANCH_NETWORK
 subnet 172.67.128.0 255.255.128.0
object network CAMPUS_NETWORK
 subnet 172.67.0.0 255.255.128.0
object network PRIVATE_NETWORK
 subnet 176.16.0.0 255.255.0.0
!
route outside 172.67.129.0 255.255.255.0 134.67.19.18 1
route inside 172.67.0.0 255.255.128.0 172.67.254.253 1
!
access-list BRANCH01_TRAFFIC extended permit tcp object CAMPUS_NETWORK object BRANCH01_NETWORK
access-list BRANCH01_TRAFFIC extended permit icmp object CAMPUS_NETWORK object BRANCH01_NETWORK
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit tcp object PRIVATE_NETWORK object PRIVATE_NETWORK
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit icmp object BRANCH_NETWORK object CAMPUS_NETWORK
!
access-group ENTERPRISE_PRIVATE-TRAFFIC out interface inside
!
crypto ipsec ikev1 transform-set L2L esp-aes esp-sha-hmac
!
crypto map BRANCH1 1 match address BRANCH01_TRAFFIC
crypto map BRANCH1 1 set peer 134.67.19.18
crypto map BRANCH1 1 set security-association lifetime seconds 86400
crypto map BRANCH1 1 set ikev1 transform-set L2L
crypto map BRANCH1 interface outside
crypto ikev1 enable outside
crypto ikev1 policy 1
 encr aes
 authentication pre-share
 group 2
!
tunnel-group 134.67.19.18 type ipsec-l2l
tunnel-group 134.67.19.18 ipsec-attributes
 ikev1 pre-shared-key fyodorov67
!
```

---

## 5. Конфигурация: ASA филиала

```text
hostname ASA-BRANCH01_19
!
interface Vlan1
 nameif inside
 security-level 100
 ip address 172.67.129.1 255.255.255.0
!
interface Vlan2
 nameif outside
 security-level 0
 ip address 134.67.19.18 255.255.255.240
!
object network BRANCH01_NETWORK
 subnet 172.67.129.0 255.255.255.0
object network BRANCH_NETWORK
 subnet 172.67.128.0 255.255.128.0
object network CAMPUS_NETWORK
 subnet 172.67.0.0 255.255.128.0
object network PRIVATE_NETWORK
 subnet 176.16.0.0 255.255.0.0
!
route outside 172.67.0.0 255.255.128.0 134.67.19.17 1
!
access-list PRIVATE_TRAFFIC extended permit tcp object BRANCH01_NETWORK object CAMPUS_NETWORK
access-list PRIVATE_TRAFFIC extended permit icmp object BRANCH01_NETWORK object CAMPUS_NETWORK
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit tcp object PRIVATE_NETWORK object PRIVATE_NETWORK
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit icmp object CAMPUS_NETWORK object BRANCH_NETWORK
!
access-group ENTERPRISE_PRIVATE-TRAFFIC out interface inside
!
crypto ipsec ikev1 transform-set L2L esp-aes esp-sha-hmac
!
crypto map BRANCH1 1 match address PRIVATE_TRAFFIC
crypto map BRANCH1 1 set peer 134.67.19.17
crypto map BRANCH1 1 set security-association lifetime seconds 86400
crypto map BRANCH1 1 set ikev1 transform-set L2L
crypto map BRANCH1 interface outside
crypto ikev1 enable outside
crypto ikev1 policy 1
 encr aes
 authentication pre-share
 group 2
!
tunnel-group 134.67.19.17 type ipsec-l2l
tunnel-group 134.67.19.17 ipsec-attributes
 ikev1 pre-shared-key fyodorov67
!
```

---

## 6. Проверка туннеля

На **обоих** ASA:

```text
show crypto isakmp sa
show crypto ipsec sa
```

Ожидается: **IKE SA** (роль Initiator/Responder, состояние вроде `QM_IDLE`), **IPsec SA** с `esp-aes 256` и ненулевыми счётчиками при генерации трафика между разрешёнными сетями.

Дополнительно:

```text
show crypto map
show access-list BRANCH01_TRAFFIC
show access-list PRIVATE_TRAFFIC
```

Проверьте **ICMP/TCP** с тестовых хостов: источник в `CAMPUS_NETWORK`, назначение в `BRANCH01_NETWORK` (и обратно) — согласно ACL.

---

## 7. Веб-сервер и DNS (требования РИП)

1. Сайт: **несколько страниц**, **навигация**, **графика**, **минимум одно поле ввода**, переходы **зависят от введённых данных**.
2. DNS: **A-запись** `www.fyodorov.iu5` на IP сервера.
3. В отчёт: скриншоты разрешения имени и открытия сайта.

---

## 8. Типичные ошибки

| Проблема | Что проверить |
|----------|----------------|
| Нет IKE SA | Совпадение PSK, `tunnel-group`, `crypto ikev1 enable outside`, IP peer, фильтрация UDP 500/4500 |
| IKE есть, нет IPsec | Совпадение ACL interesting traffic, `transform-set`, маски object |
| SA есть, нет пинга/HTTP | Статические маршруты, ACL на `inside`, NAT (если включён — может нужен exemption) |

---

## 9. Что приложить к отчёту

Схема топологии, таблица адресации (все интерфейсы и подсети), конфигурации ASA, вывод `show crypto isakmp sa` и `show crypto ipsec sa`, скриншоты DNS/веб, список имён устройств с **вариантом 19**.
