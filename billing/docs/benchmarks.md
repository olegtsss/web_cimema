# Техническое задание проекта «Биллинг»:

Нужно сделать два метода работы с картами: оплатить подписку и вернуть за неё деньги. При этом система должна быть устойчивой к перебоям: не должно происходить двойных списаний, и чтобы у пользователя всегда была гарантия, что операция выполнилась. Помимо реализации системы, интегрируйте эту систему с админкой Django, чтобы вы могли контролировать оплату подписок клиентами.

## Сформулированные функциональные требования к провайдерам в соответствии с ТЗ:

1) Возможность принятия платежей по картам от пользователей.
2) Возможность возврата средств по ранее сделанным платежам.

## Рассматриваемые провайдеры:

1) ЯПей `https://console.pay.yandex.ru/`
2) ЮКасса `https://yookassa.ru/`
3) Робокасса `https://robokassa.com`
4) Покупо `https://pokupo.ru`

### Соответствие провайдера техническому заданию:

1) `ЯПей` имеет rest api по созданию ссылки на оплату заказа, а также его последующей отмены. На стороне биллинг сервиса выполняются сответствующие http запросы, из ответов извлекается ссылка на оплату, которая передается пользователю. После оплаты `ЯПей` выполняет callback на биллинг сервис, а также имеется возможность запроса о текущем статусе платежа.
2) `ЮКасса` имеет python библиотеку для взаимодействия со своим api. На стороне биллинг сервиса создается объект заказа, одним из атрибутов которого будет являться ссылка на оплату, которая должна быть отправлена пользователю. После оплаты `ЮКасса` выполняет callback на биллинг сервис, а также имеется возможность запроса о текущем статусе платежа. Провайдер предоставляет возможность отмены платежа с возвратом денежных средств пользователю.
3) `Робокасса` имеет api интерфейс для электронной торговли. На стороне биллинг сервиса производится генерация ссылки на оплату, которая передается пользователю. При переходе по ней ему провайдером предлагается выполнить платеж банковской картой, в случае успеха `Робокасса` выполняет callback на биллинг сервис. Возврат денежных средств по платежу осуществляется через администратора сервиса `Робокасса`, api такого функционала не имеет.
4) `Покупо` имеет api интерфейс для электронной торговли. На стороне биллинг сервиса производится генерация ссылки на оплату, которая передается пользователю. При переходе по ней ему провайдером предлагается выполнить платеж банковской картой, в случае успеха `Покупо` выполняет callback на биллинг сервис. Допускается предварительный запрос для уточнения корректности оформляемого пользователем платежа. Возврат денежных средств по платежу осуществляется через администратора сервиса `Покупо`, api такого функционала не имеет.

Вывод:
`Робокасса` и `Покупо` не имеют возможности отмены платежа и возврата денежных средств пользователю в автоматическом режиме, поэтому в соответствии с техническим заданием не подходят под обозначенные требования. При этом имеющийся опыт интеграции указанных сервисов позволил бы быстрее запустить биллинг сервис.

## Возможности при работе с провайдерами:

1) `ЯПей` имеет широкие возможности по работе с платежами: полная оплата (банковской картой или СБП) и оплата частями, рекарринговые платежи и рекуррентные платежи. На текущий момент это излишне, однако в будущем может быть необходимым. Система предоставляет возможность отладки в тестовой среде. Однако достаточно высокая комиссия 4,8% с каждой транзакции (против комиссий 3,9% для `Робокасса` и `Покупо`). Хорошо документированный rest api позволяет гибко интегрировать платежную систему в разрабатываемый сервис. Имеется возможность трассировки и работы со служебными заголовками: `X-Request-Id` (уникальный идентификатор запроса), `X-Request-Timeout` (таймаут запроса) и `X-Request-Attempt` (номер попытки). 
2) `ЮКасса` также имеет достаточно широкие возможности на вырост: полная оплата и оплата частями, различные варианты приема оплаты от пользователя (банковские карты, электронные кошельки, через приложения банков, Mir Pay, кредитование, баланс телефона). При этом низкая комиссия в 3,5%. Система также предоставляет возможность отладки в тестовой среде. Собственная python библиотека по работе с сервисом позволяет легко приступить к работе с api, скрывая часть процедур, что может при определенных ситуациях усложнить интеграцию.

Вывод: `ЯПей` и `ЮКасса` имеют широкие возможности по приему платежей. При этом плюсом `ЯПей` будет являться высокая гибкость, а минусом - высокая комиссия.

## Взаимодействие с провайдерами:

`ЯПей` и `ЮКасса` позволяет запустить тестовую среду до заключения юридического договора, что удобно при интеграции в разрабатываемый сервис. Документация у обоих достаточно подробная и понятно изложенная. Нельзя исключать из виду известность Яндекса как бренда, что может располагать к себе пользователя нашего сервиса, однако `ЮКасса` предоставляет более выгодные финансовые условия по сотрудничеству.

Вывод: оптимально внедрить обе платежные системы в работу разрабатываемого биллинг сервиса, на стороне frontend-а предоставить пользователю возможность выбора, так как сценарии взаимодействия пользователя остаются одинаковые. Это одновременно обеспечит дополнительную отказоустойчивость и гибкость на будущее.

## Выводы:
1) Пользовательские сценарии для всех провайдеров будут выглядеть одинаково: предложение оплатить созданную подписку, выбор провайдера, редирект по ссылке, оплата услуги в браузере на странице провайдера, редирект на предзаданную страницу нашего сервиса.
2) Целесообразно разработать абстрактный класс для взаимодействия разрабатываемого биллинг сервиса с провайдерами платежей.
3) Выполнить интеграцию backend для обоих провайдеров в рамках заданных технических условий.
4) Логику работы по созданию подписки реализовать в биллинг сервисе.
5) В случае не получения биллинг сервисом callback вызова об успешной оплате автоматически запрашивать статус заказа у провайдера платежа.
6) Результаты работы разрабатываемого сервиса направлять в UGC сервис и сервис нотификации для уведомления пользователя об изменениях в работе (оплата подписки, активирование подписки, окончание срока подписки).

## Полученные нефункциональные требования, предъявляемые к биллинг сервису:
1) Прерывание и возобновление транзакции не должны дублировать списания или возвраты денег.
2) Средня задержка выполнения запроса api для страницы ввода реквизитов карты на стороне провайдера не должна превышать 300 мс для 90 перцентиля.
3) Средняя задержка выполнения запроса при редиректе на страницу с результатом оплаты не должна превышать 300 мс для 90 перцентиля.
4) При отказе сервисов UGC и нотификации разрабатываемому сервису продолжить работу, при отказе сервиса аутентификации прерывать свою работу.
5) Предполагаемая максимальная нагрузка  (1 млн пользователей / 30 дней / 24 часа / 60 минут * 4 запроса в рамках одного сценария) 100 запросов в секунду, средняя 1 запрос в секунду.
