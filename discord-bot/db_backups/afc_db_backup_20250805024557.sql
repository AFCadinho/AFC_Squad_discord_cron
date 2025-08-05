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

SET default_tablespace = '';

SET default_table_access_method = heap;

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
    tier character varying(16),
    discord_link text,
    always_stored boolean DEFAULT false NOT NULL,
    loaned boolean DEFAULT false NOT NULL,
    in_storage boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
-- Data for Name: loans; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.loans (id, pokemon_id, user_id, borrowed_at, returned_at) FROM stdin;
\.


--
-- Data for Name: pokemon; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.pokemon (id, name, ability, nature, tier, discord_link, always_stored, loaned, in_storage, created_at) FROM stdin;
1	Slowking-Galar	Regenerator	Sassy	ou	https://discord.com/channels/1302588750630621184/1399200070439800854	f	f	f	2025-08-04 18:39:13.524884+00
3	Alomomola	Regenerator	Relaxed	ou	https://discord.com/channels/1302588750630621184/1399200854619193364	f	f	f	2025-08-04 18:42:51.434982+00
5	Iron Valiant	Quark Drive	Naive	ou	https://discord.com/channels/1302588750630621184/1399202526070308976	f	f	f	2025-08-04 18:45:16.987116+00
7	Ceruledge	Weak Armor	Adamant	ou	https://discord.com/channels/1302588750630621184/1399203649300987974	f	f	f	2025-08-04 18:46:34.149021+00
10	Pelipper	Drizzle	Bold	ou	https://discord.com/channels/1302588750630621184/1399266879725637632	f	f	f	2025-08-04 18:50:12.785001+00
11	Skeledirge	Unaware	Careful	uu	https://discord.com/channels/1302588750630621184/1399267801117491241	f	f	f	2025-08-04 18:50:48.870282+00
12	Politoed	Drizzle	Bold	uu	https://discord.com/channels/1302588750630621184/1399420573490348215	f	f	f	2025-08-04 18:51:35.339213+00
13	Gardevoir	Trace	Timid	uu	https://discord.com/channels/1302588750630621184/1399420705098956852	f	f	f	2025-08-04 18:56:26.687572+00
14	Conkeldurr	Guts	Adamant	uu	https://discord.com/channels/1302588750630621184/1399460608897847537	f	f	f	2025-08-04 18:56:49.526052+00
15	Gyarados	Moxie	Jolly	uu	https://discord.com/channels/1302588750630621184/1399460802121044173	f	f	f	2025-08-04 18:57:16.44296+00
16	Darkrai	Bad Dreams	Timid	ou	https://discord.com/channels/1302588750630621184/1399596671025025097	f	f	f	2025-08-04 18:57:47.247322+00
17	Barraskewda	Swift Swim	Adamant	ou	https://discord.com/channels/1302588750630621184/1399597038357844120	f	f	f	2025-08-04 18:58:42.386483+00
18	Buzzwole	Beast Boost	Careful	uu	https://discord.com/channels/1302588750630621184/1399597312283508797	f	f	f	2025-08-04 18:59:57.186091+00
19	Heatran	Flash Fire	Rash	ou	https://discord.com/channels/1302588750630621184/1399805873295196170	f	f	f	2025-08-04 19:00:22.53774+00
21	Iron Bundle	Quark Drive	Timid	ou	https://discord.com/channels/1302588750630621184/1400078741245268089	f	f	f	2025-08-04 19:01:40.606322+00
22	Dragapult	Infiltrator	Naive	ou	https://discord.com/channels/1302588750630621184/1400180293763076106	f	f	f	2025-08-04 19:02:10.427184+00
24	Corviknight	Pressure	Impish	ou	https://discord.com/channels/1302588750630621184/1400181182410526841	f	f	f	2025-08-04 19:05:03.130401+00
26	Great Tusk	Protosynthesis	Jolly	ou	https://discord.com/channels/1302588750630621184/1399199801291309136	f	f	f	2025-08-04 19:06:44.828108+00
2	Bisharp	Defiant	Adamant	uu	https://discord.com/channels/1302588750630621184/1399201390617825280	f	f	f	2025-08-04 18:42:09.101679+00
4	Kingdra	Swift Swim	Modest	uu	https://discord.com/channels/1302588750630621184/1399201738724212808	f	f	f	2025-08-04 18:43:55.832426+00
8	Scizor	Technician	Brave	uu	https://discord.com/channels/1302588750630621184/1399229273235128453	f	f	f	2025-08-04 18:47:50.736275+00
9	Amoongus	Regenerator	Bold	uu	https://discord.com/channels/1302588750630621184/1399245513198665870	f	f	f	2025-08-04 18:49:10.643092+00
20	Annihilape	Defiant	Careful	uu	https://discord.com/channels/1302588750630621184/1400073663063265341	f	f	f	2025-08-04 19:00:58.425125+00
23	Gengar	Cursed Body	Timid	uu	https://discord.com/channels/1302588750630621184/1400180887567597611	f	f	f	2025-08-04 19:04:21.011493+00
25	Moltres-Galar	Berserk	Modest	uu	https://discord.com/channels/1302588750630621184/1400585815976968325	f	f	f	2025-08-04 19:05:57.377555+00
6	Garchomp	Rough Skin	Jolly	ou	https://discord.com/channels/1302588750630621184/1399203029282193579	t	f	t	2025-08-04 18:46:01.943531+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.users (id, discord_id, username, country_timezone, is_active, created_at) FROM stdin;
1	195599180624822272	Adinho	Netherlands	t	2025-08-04 19:07:30.307698+00
\.


--
-- Name: loans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: afc_squad
--

SELECT pg_catalog.setval('public.loans_id_seq', 1, false);


--
-- Name: pokemon_id_seq; Type: SEQUENCE SET; Schema: public; Owner: afc_squad
--

SELECT pg_catalog.setval('public.pokemon_id_seq', 26, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: afc_squad
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


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
-- PostgreSQL database dump complete
--

