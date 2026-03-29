# Лабораторная работа №3: IPsec VPN «сеть — сеть» (Cisco ASA 5505)

**Дисциплина:** Сетевые технологии в АСОИУ  
**Подстановка:** группа **67**, вариант **19** (ниже все адреса уже посчитаны под эти номера).

---

## Топология Packet Tracer (ваши имена устройств)

Схема: **центральная площадка** ↔ **Cloud0** (WAN/Интернет) ↔ **два филиала**.

### Центральная площадка

| Устройство | Роль |
|------------|------|
| **ASA0** (`5505`) | Межсетевой экран VPN «центр — филиалы»: **inside** → корпоративная сеть, **outside** → **Cloud0** |
| **Multilayer Switch0** (`3560-24PS`) | Ядро: к **Multilayer Switch1**, к **Switch0** и **Switch1** |
| **Multilayer Switch1** (`3560-24PS`) | Ядро: к **Multilayer Switch0**, к **Switch0(1)** и **Switch1(1)**, к **ASA0** |
| **Switch0**, **Switch1** (`2960-24TT`) | Доступ: **Server0**, **Server1** / **Server2**, **Server3** → **Multilayer Switch0** |
| **Switch0(1)**, **Switch1(1)** (`2960-24TT`) | Доступ: **Laptop0**, **Laptop1** / **Laptop2**, **Laptop3** → **Multilayer Switch1** |
| **Server0** … **Server3** | Сервисы (в т.ч. веб/DNS по заданию РИП) |
| **Laptop0** … **Laptop3** | Рабочие станции кампуса |

**Стык «кампус — ASA0»:** интерфейс **inside** у **ASA0** — в одной подсети с L3-интерфейсом **Multilayer Switch1** (или маршрутизатора за ним), см. раздел адресации.

### WAN и филиалы

| Устройство | Роль |
|------------|------|
| **Cloud0** | Имитация канала в Интернет между центром и DSL |
| **DSL Modem0** | Канал в **Cloud0** → филиал **сверху** на схеме |
| **ASA2** (`5505`) | Фаервол **филиала 1**: **outside** → **DSL Modem0**, **inside** → **Router0** |
| **Router0** (`1941`) | Внутренний маршрутизатор филиала 1 (за **ASA2**) |
| **DSL Modem1** | Канал в **Cloud0** → филиал **снизу** |
| **ASA1** (`5505`) | Фаервол **филиала 2**: **outside** → **DSL Modem1**, **inside** → **Router1** |
| **Router1** (`1941`) | Внутренний маршрутизатор филиала 2 (за **ASA1**) |

**Связь ASA — Router (красный индикатор):** на стыке **ASA2—Router0** и **ASA1—Router1** назначьте адреса из **одной** подсети на интерфейсах `inside` у ASA и WAN у маршрутизатора, выполните `no shutdown`, согласуйте скорость/duplex при необходимости. Маршрут по умолчанию на **Router0**/**Router1** — на IP **ASA** со стороны филиальной сети.

### Соответствие туннелей и адресов `outside`

| ASA | Роль | Публичный адрес (`outside`, подсеть `134.67.19.16/28`) |
|-----|------|--------------------------------------------------------|
| **ASA0** | Центр (хаб) | `134.67.19.17` |
| **ASA2** | Филиал 1 (верх на схеме) | `134.67.19.18` |
| **ASA1** | Филиал 2 (низ на схеме) | `134.67.19.19` |

На **ASA0** — **два** IPsec L2L: peer `134.67.19.18` (**ASA2**) и peer `134.67.19.19` (**ASA1**).

---

## 1. Цель работы

Настроить **два** site-to-site IPsec VPN (**ASA0** ↔ **ASA2**, **ASA0** ↔ **ASA1**) между корпоративной сетью и филиалами через **Cloud0**, обеспечить прохождение заданного трафика, настроить **маршрутизацию** на стенде (статика/OSPF — по требованию кафедры), проверить туннели командами `show`. Дополнительно: **веб-сервер** и **DNS** по РИП, в именах при необходимости указывайте **вариант 19** (например в подписи к `DSL Modem0` в отчёте: `DSL Modem_19_0`).

---

## 2. Краткая теория

### 2.1. IPsec «сеть — сеть»

Трафик между подсетями шифруется **ESP** в туннельном режиме. Сначала **IKEv1** (**ISAKMP SA**), затем **IPsec SA**. Аутентификация — **PSK** `fyodorov67`.

### 2.2. Криптография (методичка)

- **ESP AES-256** и **HMAC SHA** для ESP: `esp-aes` + `esp-sha-hmac`, политика IKE `encr aes`; в `show crypto ipsec sa` — `esp-aes 256`.

```text
crypto ipsec ikev1 transform-set L2L esp-aes esp-sha-hmac
```

### 2.3. ASA: security-level и ACL

Нужны явные **ACL** и **`ENTERPRISE_PRIVATE-TRAFFIC`** с `access-group ... out interface inside`, иначе трафик на `inside` может блокироваться.

### 2.4. Crypto map

Несколько филиалов — на **ASA0** несколько записей **одного** crypto map (разные `seq` и `set peer`). **Interesting traffic** на каждом конце должен **зеркально** совпадать по подсетям.

---

## 3. Адресация (группа 67, вариант 19)

**Правило:** второй октет **67**, третий **19** в шаблонах `172.X.Y…`, `195.X.Y…`, `134.X.Y…`.

### 3.1. Корпоративная сеть

| Зона | Подсеть |
|------|---------|
| Корпоративная сеть | `172.67.0.0/17` |
| DC | `172.67.0.0/18` |
| Пользователи | `172.67.83.0/20` |
| DMZ | `172.67.115.0/21` |
| Сетевые устройства | `172.67.71.0/23` |
| P2P L3 | `172.67.73.0/24` |

### 3.2. Локальные сети филиалов (методичка)

| Филиал на схеме | Подсеть LAN за ASA |
|-----------------|-------------------|
| Филиал 1 (**ASA2**, **Router0**) | `195.67.19.0/24` |
| Филиал 2 (**ASA1**, **Router1**) | `195.67.69.0/24` |

### 3.3. Публичные адреса ASA (`134.67.19.16/28`)

| Устройство | IP `outside` |
|------------|----------------|
| **ASA0** | `134.67.19.17/28` |
| **ASA2** | `134.67.19.18/28` |
| **ASA1** | `134.67.19.19/28` |

### 3.4. Объекты для VPN и стык ASA0 — кампус

| Object / роль | Подсеть |
|---------------|---------|
| `CAMPUS_NETWORK` | `172.67.0.0/17` → маска `255.255.128.0` |
| `BRANCH01_NETWORK` (LAN за **ASA2**) | `195.67.19.0/24` |
| `BRANCH02_NETWORK` (LAN за **ASA1**) | `195.67.69.0/24` |
| `PRIVATE_NETWORK` (как в методичке) | `176.16.0.0/16` |

**Стык ASA0 — Multilayer Switch1 (inside):**

- **ASA0** `inside`: `172.67.254.254/30`
- L3 на **Multilayer Switch1** (SVI или порт маршрутизации): `172.67.254.253/30`

Статический маршрут на **ASA0** к суммарному адресу кампуса:  
`route inside 172.67.0.0 255.255.128.0 172.67.254.253`

**Стык ASA — Router (филиалы):** пример: подсеть `195.67.19.128/30` на линке **ASA2**—**Router0** (выберите непересекающуюся с `195.67.19.0/24` для пользователей за Router0 или спланируйте разбиение сети `195.67.19.0/24` по методичке кафедры). Проще всего: вынести LAN пользователей за **Router0** в подсеть из `195.67.19.0/24`, а линк ASA—Router сделать `/30` из этой же /24 (тогда аккуратно разделите хосты). Если в лабе допускается «плоская» сеть за ASA без отдельной подсети на Router — назначьте **Router0** адрес из `195.67.19.0/24`, шлюз — **ASA2 inside** `195.67.19.1`.

Рекомендация для отчёта:

- **ASA2 inside:** `195.67.19.1/24`
- **Router0** (LAN): адрес из `195.67.19.0/24`, default `195.67.19.1`
- **ASA1 inside:** `195.67.69.1/24`
- **Router1** (LAN): адрес из `195.67.69.0/24`, default `195.67.69.1`

### 3.5. Ключ и DNS

- **PSK:** `fyodorov67` на **ASA0**, **ASA1**, **ASA2** для соответствующих `tunnel-group`.
- **DNS A:** `www.fyodorov.iu5` → IP веб-сервера (например один из **Server0**…**Server3** в DMZ `172.67.115.0/21`).

---

## 4. Конфигурация ASA0 (центр, к Multilayer Switch1 и Cloud0)

Интерфейсы в PT могут называться `Vlan1`/`Vlan2` или `Ethernet0/0` — ориентируйтесь на фактические `nameif inside` / `outside`.

```text
hostname ASA0
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
 subnet 195.67.19.0 255.255.255.0
object network BRANCH02_NETWORK
 subnet 195.67.69.0 255.255.255.0
object network CAMPUS_NETWORK
 subnet 172.67.0.0 255.255.128.0
object network PRIVATE_NETWORK
 subnet 176.16.0.0 255.255.0.0
!
route outside 195.67.19.0 255.255.255.0 134.67.19.18 1
route outside 195.67.69.0 255.255.255.0 134.67.19.19 1
route inside 172.67.0.0 255.255.128.0 172.67.254.253 1
!
access-list BRANCH01_TRAFFIC extended permit tcp object CAMPUS_NETWORK object BRANCH01_NETWORK
access-list BRANCH01_TRAFFIC extended permit icmp object CAMPUS_NETWORK object BRANCH01_NETWORK
access-list BRANCH02_TRAFFIC extended permit tcp object CAMPUS_NETWORK object BRANCH02_NETWORK
access-list BRANCH02_TRAFFIC extended permit icmp object CAMPUS_NETWORK object BRANCH02_NETWORK
!
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit tcp object PRIVATE_NETWORK object PRIVATE_NETWORK
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit icmp object BRANCH01_NETWORK object CAMPUS_NETWORK
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit icmp object BRANCH02_NETWORK object CAMPUS_NETWORK
!
access-group ENTERPRISE_PRIVATE-TRAFFIC out interface inside
!
crypto ipsec ikev1 transform-set L2L esp-aes esp-sha-hmac
!
crypto map VPN_HUB 1 match address BRANCH01_TRAFFIC
crypto map VPN_HUB 1 set peer 134.67.19.18
crypto map VPN_HUB 1 set security-association lifetime seconds 86400
crypto map VPN_HUB 1 set ikev1 transform-set L2L
crypto map VPN_HUB 2 match address BRANCH02_TRAFFIC
crypto map VPN_HUB 2 set peer 134.67.19.19
crypto map VPN_HUB 2 set security-association lifetime seconds 86400
crypto map VPN_HUB 2 set ikev1 transform-set L2L
crypto map VPN_HUB interface outside
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
tunnel-group 134.67.19.19 type ipsec-l2l
tunnel-group 134.67.19.19 ipsec-attributes
 ikev1 pre-shared-key fyodorov67
!
```

---

## 5. Конфигурация ASA2 (филиал 1: DSL Modem0, Router0)

```text
hostname ASA2
!
interface Vlan1
 nameif inside
 security-level 100
 ip address 195.67.19.1 255.255.255.0
!
interface Vlan2
 nameif outside
 security-level 0
 ip address 134.67.19.18 255.255.255.240
!
object network BRANCH01_NETWORK
 subnet 195.67.19.0 255.255.255.0
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
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit icmp object CAMPUS_NETWORK object BRANCH01_NETWORK
!
access-group ENTERPRISE_PRIVATE-TRAFFIC out interface inside
!
crypto ipsec ikev1 transform-set L2L esp-aes esp-sha-hmac
!
crypto map VPN_SPOKE 1 match address PRIVATE_TRAFFIC
crypto map VPN_SPOKE 1 set peer 134.67.19.17
crypto map VPN_SPOKE 1 set security-association lifetime seconds 86400
crypto map VPN_SPOKE 1 set ikev1 transform-set L2L
crypto map VPN_SPOKE interface outside
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

**Router0:** `ip route 0.0.0.0 0.0.0.0 195.67.19.1` (или маршрут только к сетям кампуса — по заданию). Интерфейс к **ASA2** — в `195.67.19.0/24`.

---

## 6. Конфигурация ASA1 (филиал 2: DSL Modem1, Router1)

```text
hostname ASA1
!
interface Vlan1
 nameif inside
 security-level 100
 ip address 195.67.69.1 255.255.255.0
!
interface Vlan2
 nameif outside
 security-level 0
 ip address 134.67.19.19 255.255.255.240
!
object network BRANCH02_NETWORK
 subnet 195.67.69.0 255.255.255.0
object network CAMPUS_NETWORK
 subnet 172.67.0.0 255.255.128.0
object network PRIVATE_NETWORK
 subnet 176.16.0.0 255.255.0.0
!
route outside 172.67.0.0 255.255.128.0 134.67.19.17 1
!
access-list PRIVATE_TRAFFIC extended permit tcp object BRANCH02_NETWORK object CAMPUS_NETWORK
access-list PRIVATE_TRAFFIC extended permit icmp object BRANCH02_NETWORK object CAMPUS_NETWORK
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit tcp object PRIVATE_NETWORK object PRIVATE_NETWORK
access-list ENTERPRISE_PRIVATE-TRAFFIC extended permit icmp object CAMPUS_NETWORK object BRANCH02_NETWORK
!
access-group ENTERPRISE_PRIVATE-TRAFFIC out interface inside
!
crypto ipsec ikev1 transform-set L2L esp-aes esp-sha-hmac
!
crypto map VPN_SPOKE 1 match address PRIVATE_TRAFFIC
crypto map VPN_SPOKE 1 set peer 134.67.19.17
crypto map VPN_SPOKE 1 set security-association lifetime seconds 86400
crypto map VPN_SPOKE 1 set ikev1 transform-set L2L
crypto map VPN_SPOKE interface outside
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

**Router1:** шлюз по умолчанию — `195.67.69.1` (**ASA1**).

---

## 7. Маршрутизация на Multilayer Switch0 / Multilayer Switch1

Назначьте **SVI** или интерфейсы маршрутизации в подсетях кампуса (`172.67.x.x`), маршрут **к сетям филиалов** — на `172.67.254.254` (**ASA0**), маршрут **по умолчанию** или к внешним сетям — по схеме лабораторной (статика или OSPF/EIGRP). Без согласованных маршрутов пинг с **Laptop0** до сети филиала не пойдёт, даже при поднятом IPsec.

---

## 8. Проверка туннелей

На **ASA0**, **ASA1**, **ASA2**:

```text
show crypto isakmp sa
show crypto ipsec sa
show crypto map
```

На **ASA0** должны быть **две** пары SA к `134.67.19.18` и `134.67.19.19`. Проверка трафика: **Laptop**/**Server** в `172.67.0.0/17` ↔ хосты за **Router0** / **Router1** в `195.67.19.0/24` и `195.67.69.0/24`.

```text
show access-list BRANCH01_TRAFFIC
show access-list BRANCH02_TRAFFIC
show access-list PRIVATE_TRAFFIC
```

---

## 9. Веб-сервер и DNS (РИП)

1. Сайт на одном из **Server0**…**Server3**: несколько страниц, навигация, графика, поле ввода, переходы от ввода.
2. **DNS:** A-запись `www.fyodorov.iu5` на IP сервера.
3. В отчёт: скриншоты и топология с подписями **Cloud0**, **ASA0**, **ASA1**, **ASA2**, **DSL Modem0/1**, **Multilayer Switch0/1**.

---

## 10. Типичные ошибки

| Проблема | Что проверить |
|----------|----------------|
| Красный линк ASA—Router | IP и маска на обоих концах, `no shutdown`, одна подсеть |
| Нет IKE SA | PSK, `tunnel-group`, peer, UDP 500/4500 до peer |
| Один туннель есть, второго нет | Вторая запись `crypto map` на **ASA0**, маршрут `route outside` к второй подсети |
| SA есть, нет ping | Маршруты на **Multilayer Switch1** и на **Router0**/**Router1**, ACL `inside`, NAT |

---

## 11. Что приложить к отчёту

Схема с именами **ASA0**, **ASA1**, **ASA2**, **Cloud0**, коммутаторов и серверов; таблица IP; конфигурации трёх ASA и ключевых маршрутов; `show crypto isakmp sa` / `show crypto ipsec sa` с **ASA0** (оба peer) и с филиалов.
