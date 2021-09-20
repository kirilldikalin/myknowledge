В этом документа собраны практические задачи 

Содержание:
<a id="sections"></a>

* [SQL](#sql)
* [Python](#python)
* [Статистика](#stat)

# SQL
<a id="sql"></a>
([наверх](#sections))

## Задание 1

Ты хочешь посмотреть распределение time-to-convert – отрезка времени (в днях) между заходом на сайт и оформление заказа. 

Для каждого варианта time_to_convert нужно знать

- количество заказов, которые были совершены в таким time_to_convert
- % заказов от общего числа
- кумулятивный % заказов

У тебя уже есть таблица  `mart_orders` , в которой лежат 

- **main_page_viewed_dt** – дата захода на сайт
- **order_completed_dt** – дата оформления заказа
- **order_id** – уникальный идентификатор заказа

и часть скрипта:
```
with base_table as 
(select date_diff(order_completed_dt, main_page_viewed_dt, day) as time_to_convert
        , count(order_id) as orders
from analytics.mart_orders
where order_completed_dt is not null
group by time_to_convert)

select time_to_convert
        , orders
        , (a) as percent
        , (b) as cumulative_percent
from base_table
order by time_to_convert desc
```
### 1_1. Что нужно вставить в (a)? (percent)

1. ```orders/sum(orders) over() ```
2. ```orders/sum(orders) over(order by time_to_convert) ```
3. ```orders/sum(orders)```

### 1_2. Что нужно вставить в (b) (cumulative_percent)

1. ```sum(orders) over(order by time_to_convert) / sum(orders) over()```
2. ```sum(orders) over(order by time_to_convert) / sum(orders) ```
3. ```sum(orders) over(partition by time_to_convert order by time_to_convert) / sum(orders) ```

### 1_3. Как поменять запрос, чтобы учитывать только те дни, в которых число заказов превышает 200?

1.  
```
with base_table as 
(select  date_diff(order_completed_dt, main_page_viewed_dt, day) as time_to_convert
        , count(distinct order_id) as orders
from analytics.mart_orders
where order_completed_dt is not null
      and orders > 200 -- новая строка
group by time_to_convert)

select time_to_convert
        , orders
				, (a) as percent
				, (b) as cumulative_percent
from base_table
order by time_to_convert desc
```

2.  
```
with base_table as 
(select  date_diff(order_completed_dt, main_page_viewed_dt, day) as time_to_convert
        , count(distinct order_id) as orders
from analytics.mart_orders
where order_completed_dt is not null
group by time_to_convert
having orders > 200 -- новая строка
)

select time_to_convert
        , orders
				, (a) as percent
				, (b) as cumulative_percent
from base_table
order by time_to_convert desc
```

3. Оба варианта сработают

Решение:

### 1_1

**Ответ: 1**

Использование конструкции `orders/sum(orders) over()` даст нам верные проценты!

**Пояснение**

Что нам нужно сделать, чтобы получить % заказов от общего числа? 

Количество заказов за интервал времени, каждый раз делить на количество всех заказов. 

При создании таблицы `base_table` мы группируем по интервалу, значит переменная `orders` содержит в себе количество заказов за интервал времени. Теперь нам нужно получить количество всех заказов. Из-за того, что мы ничего не указываем в `over()`, отсутствует внутреннее деление на блоки и оконная функция будет возвращать максимальное значение количества заказов на всём диапазоне выборки.

Что же будет, если мы попробуем использовать другие конструкции? 

- Использовать выражение `orders/sum(orders)` не очень правильно. Учитывая, что при группировке `orders` и `sum(orders)` это одно и тоже число, в результате получим столбец единиц.
- Использовать выражение `orders/sum(orders) over(order by time_to_convert)` также неправильно, из-за определения логического порядка строк мы получим значения никак не связанные с заказами.

### 1_2

**Ответ: 1**

**Пояснение**

Кумулятивный % заказов, он же накопительный процент рассчитывается путём прибавления процента к сумме предыдущих процентов. Для этого необходимо сумму заказов до определённого интервала делить на количество всех заказов. Это уже говорит нам о том, что в знаменателе должно использоваться тоже выражение, что и в первом случае. Конструкция в числителе будет считать количество заказов за интервал включая в него все, которые меньше, что нам и надо.

Рассмотрим применение других выражений:

- `sum(orders) over(partition by time_to_convert order by time_to_convert)` это выражение группирует и сортирует по `time_to_convert` , а значит не будет отличаться от `sum(orders)`  так что получим столбик единиц.
- `sum(orders) over(order by time_to_convert) / sum(orders)` деление на `sum(orders)` (количество заказов за интервал )даст нам значения не имеющие никакого смысла.

# Python
<a id="python"></a>
([наверх](#sections))

# Статистика
<a id="stat"></a>
([наверх](#sections))
