--
-- PostgreSQL database dump
--

-- Dumped from database version 15.6 (Debian 15.6-1.pgdg120+2)
-- Dumped by pg_dump version 15.6 (Debian 15.6-1.pgdg120+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS public;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: notification_statuses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_statuses (
    notification_id uuid NOT NULL,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    notification_id uuid NOT NULL,
    source_id uuid NOT NULL,
    user_id uuid NOT NULL,
    template_id uuid,
    delivery_mode character varying(50) NOT NULL,
    channel character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.templates (
    template_id uuid NOT NULL,
    title character varying(120) NOT NULL,
    description character varying(500),
    body text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Data for Name: notification_statuses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notification_statuses (notification_id, status, created_at) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notifications (notification_id, source_id, user_id, template_id, delivery_mode, channel, created_at) FROM stdin;
\.


--
-- Data for Name: templates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.templates (template_id, title, description, body, created_at) FROM stdin;
76af789b-3d56-4799-b610-88f4d013b53e	Weekly compilation (v1)	Недельная подборка фильмов	<!DOCTYPE html>\n<html>\n\t<body>\n\t\t<div class="container">\n\t\t\t<header><h1>Еженедельная подборка произведений</h1></header>\n\t\t\t<main>\n\t\t\t\t<p>Привет, {{ first_name }}!</p>\n        <p>Мы подобрали для тебя:</p>\n        <ul>\n          <li>Фильм 1</li>\n          <li>Фильм 2</li>\n          <li>Фильм 3</li>\n          <li>Фильм 4</li>\n          <li>Фильм 5</li>\n          <li>Фильм 6</li>\n        </ul>\n\t\t\t</main>\n      <footer><p>Твой <b>Practix</b> :)</p></footer>\n\t\t</div>\n\t</body>\n</html>\n	2024-05-07 08:23:36.757957+00
1106a6fa-8520-44c7-bb2e-fabc51a9440b	Register (v1)	Регистрация пользователя	<!DOCTYPE html>\n<html>\n\t<body>\n\t\t<div class="container">\n\t\t\t<header><h1>Регистрация в Practix</h1></header>\n\t\t\t<main>\n\t\t\t\t<p>Привет, {{ first_name }}!</p>\n        <p>Рады видеть тебя в числе новых зрителей. Надеемся, что тебе тут понравится.</p>\n\t\t\t</main>\n      <footer><p>Твой <b>Practix</b> :)</p></footer>\n\t\t</div>\n\t</body>\n</html>\n	2024-05-07 08:23:40.008597+00
8068b4f0-c361-4cab-a377-99c214f36d8f	Monthly statistics (v1)	Месячная статистика пользователя	<!DOCTYPE html>\n<html>\n\t<body>\n\t\t<div class="container">\n\t\t<header><h1>Ежемесячная статистика просмотра</h1></header>\n\t\t\t<main>\n\t\t\t\t<p>Привет, {{ first_name }}!</p>\n        <p>В этом месяце ты посмотрел N фильмов. Большая часть из них - детективы.</p>\n        <p>Поздравляем! Ваше звание - Эркюль Пуаро!</p>\n\t\t\t</main>\n      <footer><p>Твой <b>Practix</b> :)</p></footer>\n\t\t</div>\n\t</body>\n</html>\n	2024-05-07 08:23:43.587515+00
\.


--
-- Name: notification_statuses notification_statuses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_statuses
    ADD CONSTRAINT notification_statuses_pkey PRIMARY KEY (notification_id, status);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);


--
-- Name: templates templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_pkey PRIMARY KEY (template_id);


--
-- Name: templates templates_title_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_title_key UNIQUE (title);


--
-- PostgreSQL database dump complete
--

