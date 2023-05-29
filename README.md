# Условия использования 

Применять только в учебных целях. Данных код может содержать ошибки, авторы не несут никакой ответственности за любые последствия использования этого кода.
Условия использования и распространения - MIT лицензия (см. файл LICENSE).

## Настройка и запуск

### Системные требования

Данный пример разработан и проверен на ОС Ubuntu 20.04.5, авторы предполагают, что без каких-либо изменений этот код может работать на любых Debian-подобных OS, для других Linux систем, а также для MAC OS необходимо использовать другой менеджер пакетов. В Windows необходимо самостоятельно установить необходимое ПО или воспользоваться виртуальной машиной с Ubuntu (также можно использовать WSL версии не ниже 2).

Описание настройки инфраструктуры для разработки можно найти во втором разделе короткого курса на степике https://stepik.org/course/133991/ 

### Используемое ПО

Стандартный способ запуска демо предполагает наличие установленного пакета *docker*, а также *docker-compose*. Для автоматизации типовых операций используется утилита *make*, хотя можно обойтись и без неё, вручную выполняя соответствующие команды из файла Makefile в командной строке.

Другое используемое ПО (в Ubuntu будет установлено автоматически, см. следующий раздел):
- python (желательно версия не ниже 3.8)
- pipenv (для виртуальных окружений python)

Для работы с кодом примера рекомендуется использовать VS Code или PyCharm.

В случае использования VS Code следует установить расширения
- REST client
- Docker
- Python

### Настройка окружения и запуск примера

В терминале перейдите в папку проекта и выполните команду

```bash
make all
```

В результате будет создано виртуальное окружение для этого проекта, собраны необходимые docker образы, запущен пример и автоматический тест.

Вывод должен быть похож на изображённый в следующей картинке, числа могут отличаться, т.к. генерируются случайным образом.

![Результат выполнения команды](./docs/images/run-results.png)

### Компоненты

| Название | Назначение | Комментарий |
|----|----|----|
|*device* | Непосредственно устройство детектирования. Принимает данные от аналогового датчика (sensor), передает сообщения на Пульт управления (scada), обрабатывает процедуры обновления и т.д. | - |
|*file_server* | Поскольку в реализации подразумевалось, что инженеры загружают обновление напрямую в устройство, то для эмуляции этого процесса был использован данный компонент. Его стоит рассматривать как подключенное к device устройство, с которого при успешной аутентификации ключей скачивается на device обновление. Поэтому в т.ч. обладает своей памятью в ./data, где и лежит "обновление". | - |
|*protection_system* | Эмулятор системы защиты станции. При выявлении превышающего порог значения в device, сюда отправляется сообщение, чтобы "сработала" защита. | - |
|*scada*  | Эмулятор пульта управления станцией. Получает все данные (значения, сообщения об ошибках и т.д.) от device.  | - |
|*sensor* | Эмулятор аналогового датчика, который раз в заданное время подает сгенерированный в заданном диапазоне сигнал через HTTP в device.  | - |
|*storage* | Фактически это лишь папка с данными, которая является эмулятором некоторой физической памяти устройства device. | - |

### REST запросы

Для ручного тестирования в VS Code откройте файл requests.rest, при наведении мышкой на GET и POST запросы появится текст 'Send request', при нажатии на него запрос будет выполнен.

Диаграмма последовательности данного примера имеет следующий вид:

![Диаграмма последовательности](./docs/images/nf.png)

[Cсылка на диаграмму для редактирования](//www.plantuml.com/plantuml/uml/N8f12iD024NtSuevIc_G8mGnFo0aewWDzFQjp6hYol_UUqMIv-SwMoDEzJxlRN2gIT6rsJyH5gEHVSSjZEBpM-GX9xQ0t_0gZbYikIOuHSSMtqXSrTZQ1DDEnHyOurTQ5UH63GJ1-xnYxei_m07n699Jn4Ro1-A5nIiPaGiI28b0o0SS4fE9ZUqlTF-8wcwpzjfUoL4ETYOptTLLNJtUsDZOohcrZrvr55QhbvwkUKCvN_36sMP_ZCCVV44D_QO2VqlAFTMKKqM1KpoN7cUtL6j4HGLMWHxTsNfzxkbgV89mpNwaUzdWRAxUTyt89RQLqhoZW0sKTYTdySaafUT_9EdjczaSyFXB3PW4hEw4A2V02Pfa0cuueHR2Tt8w1p9HI8Ndzwgmakqnct1KmWs8v0CKW-MCjmU0Bu2eJXJq8BHXsZkin1TmRV3ghCmWBgZspWiS6zDQsoJT0lb6mftDnMhLBGw8VKPSBLvHiM0wEeGeqh9sNAYEdKaRec1-TVn-MH1mxgOc8sJ4uh-efxiwG4NiJsaYsbVnHstQnft788v7IkpBpBhirWTblm7a4wSUE0Ll9OHJh18gHPJwehvze62NntoQHpaI3ES1HBTgVOD_SavwVGDjfzQoBqYswKjcBYbVkjDuUkyu6qmmPtfTfO3W8B7q560gNI4vYXPzBLfrenKL5FRGow_ODGHiTLhhqUMmrWuXbr-k-NnOFhBaAprOppZjiqlpYV9d-Bq4_5bZCBRa7az5V_Q5-Wy0PqwLkzTuuzVi7m00)


В соответствии с ней, логическая последовательность команд следующая: start -> { 2 * key_in (Не важен порядок) -> { 2 * key_out (Извлекать их не обязательно для завершения обновления, но желательно для корректной обработки состояний системы) }} -> stop

_Start_ загрузит приложение, уставки, настройки.

_Key in_ имитирует подключение аппаратного ключа, ключей два - Security - для специалиста по безопасности, Technical - для техника. 

Процесс обновления начинается в тот момент, когда оба ключа оказываются активированы.

_Key out_ имитирует извлечение ключа, что необходимо для корректного отображения состояния системы и ее продолжительной работы без перезапусков через start/stop.

_Stop_ останавливает все внутренние процессы и очищает значение переменных.

## Примечания

В данном примере не используется брокер сообщений, взаимодействие между системами построено на базе REST запросов, однако в решении _внутренние_ компоненты проектируемого устройства должны взаимодействовать через брокер сообщений (желательно Apache Kafka), _внешнее_ взаимодействие следует по-прежнему через REST. 

Пример такой реализации можно найти в репозитории https://github.com/sergey-sobolev/secure-update, подробное описание запуска примера есть на степике (https://stepik.org/course/133991/)

Хотя код этого примера написан на Python, команды могут по желанию своё решение сделать на других языках (C/C++, C#, Golang, Javascript/Typescript, Java, Rust, PHP), основные требования:
1. использование брокера сообщений (предпочтительно Apache Kafka, но можно RabbitMQ, Mosquitto)
2. наличие хотя бы одного функционального теста
3. наличие тестов безопасности (предпочтительно автоматизированных, в крайнем случае - описание ручных тестов безопасности)
4. наличие монитора безопасности, который должен контролировать все взаимодействия между доменами безопасности
5. наличие политик безопасности, которые использует монитор безопасности. Политики безопасности должны обеспечивать реализацию предложенной политики архитектуры.

## Дополнительные материалы по кибериммунной разработке

- Видео на youtube (записи занятий)
  - Теория https://youtu.be/hTDBLP1Jlc0 
  - Разбор домашнего задания на проектирование; ключевые принципы и технологии работы кибериммунных систем https://youtu.be/eYr-toUUQDA
  - Пошаговый разбор трансформации примера в новую систему https://youtu.be/BH2HrPltr7M
  - Тестирование, в т.ч. тесты безопасности https://youtu.be/BEVZVm6xi-M 
- Github wiki по теме со ссылками на примеры и решения на Python и Java https://github.com/sergey-sobolev/cyberimmune-systems/wiki/%D0%9A%D0%B8%D0%B1%D0%B5%D1%80%D0%B8%D0%BC%D0%BC%D1%83%D0%BD%D0%B8%D1%82%D0%B5%D1%82
- Заготовка описания решения команды https://github.com/sergey-sobolev/secure-update/blob/main/docs/report/report.md
#   C y b e r i m m u n i t y  
 