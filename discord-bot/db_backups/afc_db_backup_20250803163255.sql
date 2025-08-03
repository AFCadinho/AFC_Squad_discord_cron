--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Debian 16.9-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Debian 16.9-1.pgdg110+1)

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
-- Name: public; Type: SCHEMA; Schema: -; Owner: afc_squad
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO afc_squad;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: afc_squad
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: afc_squad
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO afc_squad;

--
-- Name: loans; Type: TABLE; Schema: public; Owner: afc_squad
--

CREATE TABLE public.loans (
    id integer NOT NULL,
    pokemon_id integer NOT NULL,
    user_id integer NOT NULL,
    borrowed_at timestamp with time zone DEFAULT now() NOT NULL,
    returned_at timestamp with time zone
);


ALTER TABLE public.loans OWNER TO afc_squad;

--
-- Name: loans_id_seq; Type: SEQUENCE; Schema: public; Owner: afc_squad
--

CREATE SEQUENCE public.loans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loans_id_seq OWNER TO afc_squad;

--
-- Name: loans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: afc_squad
--

ALTER SEQUENCE public.loans_id_seq OWNED BY public.loans.id;


--
-- Name: pokemon; Type: TABLE; Schema: public; Owner: afc_squad
--

CREATE TABLE public.pokemon (
    id integer NOT NULL,
    name character varying(64) NOT NULL,
    ability character varying(64) NOT NULL,
    nature character varying(16) NOT NULL,
    discord_link text,
    loaned boolean DEFAULT false NOT NULL,
    in_storage boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    tier character varying(16),
    always_stored boolean DEFAULT false NOT NULL
);


ALTER TABLE public.pokemon OWNER TO afc_squad;

--
-- Name: pokemon_id_seq; Type: SEQUENCE; Schema: public; Owner: afc_squad
--

CREATE SEQUENCE public.pokemon_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pokemon_id_seq OWNER TO afc_squad;

--
-- Name: pokemon_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: afc_squad
--

ALTER SEQUENCE public.pokemon_id_seq OWNED BY public.pokemon.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: afc_squad
--

CREATE TABLE public.users (
    id integer NOT NULL,
    discord_id bigint NOT NULL,
    username character varying(64) NOT NULL,
    country_timezone character varying(64),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.users OWNER TO afc_squad;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: afc_squad
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO afc_squad;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: afc_squad
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: loans id; Type: DEFAULT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.loans ALTER COLUMN id SET DEFAULT nextval('public.loans_id_seq'::regclass);


--
-- Name: pokemon id; Type: DEFAULT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.pokemon ALTER COLUMN id SET DEFAULT nextval('public.pokemon_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.alembic_version (version_num) FROM stdin;
357d7312af9a
\.


--
-- Data for Name: loans; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.loans (id, pokemon_id, user_id, borrowed_at, returned_at) FROM stdin;
\.


--
-- Data for Name: pokemon; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.pokemon (id, name, ability, nature, discord_link, loaned, in_storage, created_at, tier, always_stored) FROM stdin;
4	Lokix	Swarm	Adamant	https://discord.com/channels/1252628341220053013/1262875088605155358	f	f	2025-08-02 23:36:54.016845+00	UU	f
2	Scizor	Swarm	Adamant	https://discord.com/channels/1252628341220053013/1401285165019566132	f	t	2025-08-02 22:35:08.721747+00	OU	f
3	Garchomp	Rough skin	Jolly	https://discord.com/channels/1252628341220053013/1262875088605155358	f	t	2025-08-02 23:27:37.251596+00	OU	f
5	Darkrai	Bad Dreams	Timid	https://discord.com/channels/1252628341220053013/1262875088605155358	f	t	2025-08-02 23:47:01.027283+00	OU	f
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.users (id, discord_id, username, country_timezone, created_at, is_active) FROM stdin;
2	195599180624822272	Adinho	Netherlands	2025-08-02 18:47:44.661542+00	f
\.


--
-- Name: loans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: afc_squad
--

SELECT pg_catalog.setval('public.loans_id_seq', 1, false);


--
-- Name: pokemon_id_seq; Type: SEQUENCE SET; Schema: public; Owner: afc_squad
--

SELECT pg_catalog.setval('public.pokemon_id_seq', 5, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: afc_squad
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: loans loans_pkey; Type: CONSTRAINT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_pkey PRIMARY KEY (id);


--
-- Name: pokemon pokemon_pkey; Type: CONSTRAINT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.pokemon
    ADD CONSTRAINT pokemon_pkey PRIMARY KEY (id);


--
-- Name: users users_discord_id_key; Type: CONSTRAINT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_discord_id_key UNIQUE (discord_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: loans loans_pokemon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_pokemon_id_fkey FOREIGN KEY (pokemon_id) REFERENCES public.pokemon(id);


--
-- Name: loans loans_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: afc_squad
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: afc_squad
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

