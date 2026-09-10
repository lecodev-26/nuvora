--
-- PostgreSQL database dump
--

\restrict qXSReb5goHXn5R0WzBbt6Wglb7Sj7RtWFKKxBKQqfKotX0hEhgMOEx25KEPQFyF

-- Dumped from database version 18.6 (Debian 18.6-1.pgdg12+2)
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: nuvora_db_ew1q_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO nuvora_db_ew1q_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bots; Type: TABLE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE TABLE public.bots (
    id integer NOT NULL,
    user_id integer,
    name character varying(100) NOT NULL,
    description text,
    business_name character varying(200),
    business_type character varying(50),
    nicho_id character varying(50),
    restaurant_name character varying(200),
    owner_email character varying(100),
    goal text,
    instructions text,
    personality character varying(100),
    tone character varying(100),
    greeting text,
    fallback_message text,
    answer_mode character varying(20),
    is_published boolean,
    is_active boolean,
    plan character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.bots OWNER TO nuvora_db_ew1q_user;

--
-- Name: bots_id_seq; Type: SEQUENCE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE SEQUENCE public.bots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bots_id_seq OWNER TO nuvora_db_ew1q_user;

--
-- Name: bots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER SEQUENCE public.bots_id_seq OWNED BY public.bots.id;


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE TABLE public.conversations (
    id integer NOT NULL,
    bot_id integer NOT NULL,
    channel character varying(30),
    session_id character varying(100),
    question text NOT NULL,
    answer text,
    was_answered boolean,
    workflow_id integer,
    meta text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.conversations OWNER TO nuvora_db_ew1q_user;

--
-- Name: conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE SEQUENCE public.conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.conversations_id_seq OWNER TO nuvora_db_ew1q_user;

--
-- Name: conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER SEQUENCE public.conversations_id_seq OWNED BY public.conversations.id;


--
-- Name: memories; Type: TABLE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE TABLE public.memories (
    id integer NOT NULL,
    bot_id integer NOT NULL,
    category_id integer,
    fact text NOT NULL,
    keyword character varying(100) NOT NULL,
    source character varying(20),
    is_confirmed boolean,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.memories OWNER TO nuvora_db_ew1q_user;

--
-- Name: memories_id_seq; Type: SEQUENCE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE SEQUENCE public.memories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.memories_id_seq OWNER TO nuvora_db_ew1q_user;

--
-- Name: memories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER SEQUENCE public.memories_id_seq OWNED BY public.memories.id;


--
-- Name: memory_categories; Type: TABLE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE TABLE public.memory_categories (
    id integer NOT NULL,
    bot_id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    icon character varying(10),
    "order" integer,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.memory_categories OWNER TO nuvora_db_ew1q_user;

--
-- Name: memory_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE SEQUENCE public.memory_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.memory_categories_id_seq OWNER TO nuvora_db_ew1q_user;

--
-- Name: memory_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER SEQUENCE public.memory_categories_id_seq OWNED BY public.memory_categories.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(100) NOT NULL,
    hashed_password character varying(200) NOT NULL,
    full_name character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    is_active integer,
    trial_start timestamp with time zone,
    trial_end timestamp with time zone,
    service_status character varying(20),
    payment_date timestamp with time zone,
    expiration_date timestamp with time zone,
    stripe_customer_id character varying(100)
);


ALTER TABLE public.users OWNER TO nuvora_db_ew1q_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO nuvora_db_ew1q_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: bots id; Type: DEFAULT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.bots ALTER COLUMN id SET DEFAULT nextval('public.bots_id_seq'::regclass);


--
-- Name: conversations id; Type: DEFAULT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.conversations ALTER COLUMN id SET DEFAULT nextval('public.conversations_id_seq'::regclass);


--
-- Name: memories id; Type: DEFAULT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.memories ALTER COLUMN id SET DEFAULT nextval('public.memories_id_seq'::regclass);


--
-- Name: memory_categories id; Type: DEFAULT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.memory_categories ALTER COLUMN id SET DEFAULT nextval('public.memory_categories_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: bots; Type: TABLE DATA; Schema: public; Owner: nuvora_db_ew1q_user
--

COPY public.bots (id, user_id, name, description, business_name, business_type, nicho_id, restaurant_name, owner_email, goal, instructions, personality, tone, greeting, fallback_message, answer_mode, is_published, is_active, plan, created_at, updated_at) FROM stdin;
1	1	Bot Producción	\N	Mi Negocio Real	test	desde_cero	Mi Negocio Real	prod_test@nuvora.com	Probar producción	\N	cercano	amigable	\N	\N	strict	f	t	free	2026-09-10 09:51:37.93863+00	2026-09-10 09:51:37.93863+00
\.


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: nuvora_db_ew1q_user
--

COPY public.conversations (id, bot_id, channel, session_id, question, answer, was_answered, workflow_id, meta, created_at) FROM stdin;
1	1	widget	prod_test_session	¿A qué hora abrís?	Mi negocio abre de 9:00 a 18:00	t	\N	\N	2026-09-10 09:51:56.373157+00
2	1	dashboard	\N	¿Tenéis parking?	No tengo esa información en mi memoria. Te recomiendo contactar directamente con el negocio.	f	\N	\N	2026-09-10 09:52:02.494584+00
\.


--
-- Data for Name: memories; Type: TABLE DATA; Schema: public; Owner: nuvora_db_ew1q_user
--

COPY public.memories (id, bot_id, category_id, fact, keyword, source, is_confirmed, created_at) FROM stdin;
1	1	\N	Mi negocio abre de 9:00 a 18:00	horario	manual	t	2026-09-10 09:51:44.408621+00
\.


--
-- Data for Name: memory_categories; Type: TABLE DATA; Schema: public; Owner: nuvora_db_ew1q_user
--

COPY public.memory_categories (id, bot_id, name, description, icon, "order", created_at) FROM stdin;
1	1	Horarios	Horarios de atención	🕐	1	2026-09-10 09:51:50.348708+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: nuvora_db_ew1q_user
--

COPY public.users (id, email, hashed_password, full_name, created_at, is_active, trial_start, trial_end, service_status, payment_date, expiration_date, stripe_customer_id) FROM stdin;
1	prod_test@nuvora.com	$5$rounds=535000$H.mzk.Vmn4va8O8Q$ELG/cQP0iPm7sHBayRnS4C3.zm7AWjK4xa6.fVB9hE3	Prod Test	2026-09-10 09:48:37.138971+00	1	2026-09-10 09:48:38.771743+00	2026-10-10 09:48:38.771743+00	trial	\N	\N	\N
2	prod_test2@nuvora.com	$5$rounds=535000$g7Af1XEDph7icPOV$QzC.H0WZGCxliq6cfcC/Jnea5/Yup/fPT0v5Qm.CBh9	Prod Test 2	2026-09-10 09:52:48.394897+00	1	2026-09-10 09:52:50.166285+00	2026-10-10 09:52:50.166285+00	trial	\N	\N	\N
\.


--
-- Name: bots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nuvora_db_ew1q_user
--

SELECT pg_catalog.setval('public.bots_id_seq', 1, true);


--
-- Name: conversations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nuvora_db_ew1q_user
--

SELECT pg_catalog.setval('public.conversations_id_seq', 2, true);


--
-- Name: memories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nuvora_db_ew1q_user
--

SELECT pg_catalog.setval('public.memories_id_seq', 1, true);


--
-- Name: memory_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nuvora_db_ew1q_user
--

SELECT pg_catalog.setval('public.memory_categories_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nuvora_db_ew1q_user
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: bots bots_pkey; Type: CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.bots
    ADD CONSTRAINT bots_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: memories memories_pkey; Type: CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.memories
    ADD CONSTRAINT memories_pkey PRIMARY KEY (id);


--
-- Name: memory_categories memory_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.memory_categories
    ADD CONSTRAINT memory_categories_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_bots_user_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX idx_bots_user_id ON public.bots USING btree (user_id);


--
-- Name: idx_categories_bot_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX idx_categories_bot_id ON public.memory_categories USING btree (bot_id);


--
-- Name: idx_conversations_channel; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX idx_conversations_channel ON public.conversations USING btree (channel);


--
-- Name: idx_memories_category_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX idx_memories_category_id ON public.memories USING btree (category_id);


--
-- Name: ix_bots_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_bots_id ON public.bots USING btree (id);


--
-- Name: ix_bots_owner_email; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_bots_owner_email ON public.bots USING btree (owner_email);


--
-- Name: ix_bots_user_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_bots_user_id ON public.bots USING btree (user_id);


--
-- Name: ix_conversations_bot_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_conversations_bot_id ON public.conversations USING btree (bot_id);


--
-- Name: ix_conversations_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_conversations_id ON public.conversations USING btree (id);


--
-- Name: ix_conversations_session_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_conversations_session_id ON public.conversations USING btree (session_id);


--
-- Name: ix_memories_bot_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_memories_bot_id ON public.memories USING btree (bot_id);


--
-- Name: ix_memories_category_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_memories_category_id ON public.memories USING btree (category_id);


--
-- Name: ix_memories_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_memories_id ON public.memories USING btree (id);


--
-- Name: ix_memory_categories_bot_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_memory_categories_bot_id ON public.memory_categories USING btree (bot_id);


--
-- Name: ix_memory_categories_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_memory_categories_id ON public.memory_categories USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: nuvora_db_ew1q_user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: bots bots_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.bots
    ADD CONSTRAINT bots_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: conversations conversations_bot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.bots(id);


--
-- Name: memories memories_bot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.memories
    ADD CONSTRAINT memories_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.bots(id);


--
-- Name: memories memories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.memories
    ADD CONSTRAINT memories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.memory_categories(id);


--
-- Name: memory_categories memory_categories_bot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nuvora_db_ew1q_user
--

ALTER TABLE ONLY public.memory_categories
    ADD CONSTRAINT memory_categories_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.bots(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON SEQUENCES TO nuvora_db_ew1q_user;


--
-- Name: DEFAULT PRIVILEGES FOR TYPES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TYPES TO nuvora_db_ew1q_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON FUNCTIONS TO nuvora_db_ew1q_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TABLES TO nuvora_db_ew1q_user;


--
-- PostgreSQL database dump complete
--

\unrestrict qXSReb5goHXn5R0WzBbt6Wglb7Sj7RtWFKKxBKQqfKotX0hEhgMOEx25KEPQFyF

