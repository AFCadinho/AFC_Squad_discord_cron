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
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);



--
--

CREATE TABLE public.loans (
    id integer NOT NULL,
    pokemon_id integer NOT NULL,
    user_id integer NOT NULL,
    borrowed_at timestamp with time zone DEFAULT now() NOT NULL,
    returned_at timestamp with time zone
);



--
--

CREATE SEQUENCE public.loans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
--

ALTER SEQUENCE public.loans_id_seq OWNED BY public.loans.id;


--
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



--
--

CREATE SEQUENCE public.pokemon_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
--

ALTER SEQUENCE public.pokemon_id_seq OWNED BY public.pokemon.id;


--
--

CREATE TABLE public.tournament_matches (
    id integer NOT NULL,
    tournament_id integer NOT NULL,
    participant1_id integer,
    participant2_id integer,
    challonge_id integer NOT NULL,
    round integer NOT NULL,
    completed boolean DEFAULT false NOT NULL,
    winner_participant_id integer,
    score text
);



--
--

CREATE SEQUENCE public.tournament_matches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
--

ALTER SEQUENCE public.tournament_matches_id_seq OWNED BY public.tournament_matches.id;


--
--

CREATE TABLE public.tournament_participants (
    tournament_id integer NOT NULL,
    user_id integer NOT NULL,
    challonge_id integer,
    id integer NOT NULL
);



--
--

CREATE SEQUENCE public.tournament_participants_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
--

ALTER SEQUENCE public.tournament_participants_id_seq OWNED BY public.tournament_participants.id;


--
--

CREATE TABLE public.tournaments (
    id integer NOT NULL,
    challonge_id integer NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    url text NOT NULL,
    ongoing boolean DEFAULT false NOT NULL,
    winner_id integer,
    current_tournament boolean DEFAULT false NOT NULL
);



--
--

CREATE SEQUENCE public.tournaments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
--

ALTER SEQUENCE public.tournaments_id_seq OWNED BY public.tournaments.id;


--
--

CREATE TABLE public.users (
    id integer NOT NULL,
    discord_id bigint NOT NULL,
    username character varying(64) NOT NULL,
    country_timezone character varying(64),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    pvp_experience text DEFAULT 'novice'::character varying NOT NULL
);



--
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
--

ALTER TABLE ONLY public.loans ALTER COLUMN id SET DEFAULT nextval('public.loans_id_seq'::regclass);


--
--

ALTER TABLE ONLY public.pokemon ALTER COLUMN id SET DEFAULT nextval('public.pokemon_id_seq'::regclass);


--
--

ALTER TABLE ONLY public.tournament_matches ALTER COLUMN id SET DEFAULT nextval('public.tournament_matches_id_seq'::regclass);


--
--

ALTER TABLE ONLY public.tournament_participants ALTER COLUMN id SET DEFAULT nextval('public.tournament_participants_id_seq'::regclass);


--
--

ALTER TABLE ONLY public.tournaments ALTER COLUMN id SET DEFAULT nextval('public.tournaments_id_seq'::regclass);


--
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.alembic_version (version_num) FROM stdin;
1c9346b310ec
\.


--
-- Data for Name: loans; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.loans (id, pokemon_id, user_id, borrowed_at, returned_at) FROM stdin;
\.


--
-- Data for Name: pokemon; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.pokemon (id, name, ability, nature, tier, discord_link, always_stored, loaned, in_storage, created_at) FROM stdin;
11	Skeledirge	Unaware	Careful	uu	https://discord.com/channels/1302588750630621184/1399267801117491241	f	f	f	2025-08-04 18:50:48.870282+00
14	Conkeldurr	Guts	Adamant	uu	https://discord.com/channels/1302588750630621184/1399460608897847537	f	f	f	2025-08-04 18:56:49.526052+00
16	Darkrai	Bad Dreams	Timid	ou	https://discord.com/channels/1302588750630621184/1399596671025025097	f	f	f	2025-08-04 18:57:47.247322+00
18	Buzzwole	Beast Boost	Careful	uu	https://discord.com/channels/1302588750630621184/1399597312283508797	f	f	f	2025-08-04 18:59:57.186091+00
21	Iron Bundle	Quark Drive	Timid	ou	https://discord.com/channels/1302588750630621184/1400078741245268089	f	f	f	2025-08-04 19:01:40.606322+00
22	Dragapult	Infiltrator	Naive	ou	https://discord.com/channels/1302588750630621184/1400180293763076106	f	f	f	2025-08-04 19:02:10.427184+00
12	Politoed	Drizzle	Bold	uu	https://discord.com/channels/1302588750630621184/1399420573490348215	f	f	f	2025-08-04 18:51:35.339213+00
13	Gardevoir	Trace	Timid	uu	https://discord.com/channels/1302588750630621184/1399420705098956852	f	f	f	2025-08-04 18:56:26.687572+00
15	Gyarados	Moxie	Jolly	uu	https://discord.com/channels/1302588750630621184/1399460802121044173	f	f	f	2025-08-04 18:57:16.44296+00
20	Annihilape	Defiant	Careful	uu	https://discord.com/channels/1302588750630621184/1400073663063265341	f	f	f	2025-08-04 19:00:58.425125+00
23	Gengar	Cursed Body	Timid	uu	https://discord.com/channels/1302588750630621184/1400180887567597611	f	f	f	2025-08-04 19:04:21.011493+00
25	Moltres-Galar	Berserk	Modest	uu	https://discord.com/channels/1302588750630621184/1400585815976968325	f	f	f	2025-08-04 19:05:57.377555+00
31	Tyranitar	Sand Stream	Adamant	ou	https://discord.com/channels/1302588750630621184/1415391979402952795	f	f	f	2025-09-10 17:43:28.267987+00
2	Bisharp	Defiant	Adamant	uu	https://discord.com/channels/1302588750630621184/1399201390617825280	f	f	f	2025-08-04 18:42:09.101679+00
32	Archaludon	Stamina	Modest	ou	https://discord.com/channels/1302588750630621184/1415755252463829144	f	f	f	2025-09-11 17:47:26.953684+00
8	Scizor	Technician	Brave	uu	https://discord.com/channels/1302588750630621184/1399229273235128453	f	f	f	2025-08-04 18:47:50.736275+00
9	Amoongus	Regenerator	Bold	uu	https://discord.com/channels/1302588750630621184/1399245513198665870	f	f	f	2025-08-04 18:49:10.643092+00
33	Glimmora	Toxic Debris	Timid	ou	https://discord.com/channels/1302588750630621184/1416150350049579088	f	f	f	2025-09-12 19:57:12.222561+00
6	Garchomp	Rough Skin	Jolly	ou	https://discord.com/channels/1302588750630621184/1399203029282193579	t	f	t	2025-08-04 18:46:01.943531+00
19	Heatran	Flash Fire	Rash	ou	https://discord.com/channels/1302588750630621184/1399805873295196170	t	f	t	2025-08-04 19:00:22.53774+00
5	Iron Valiant	Quark Drive	Naive	ou	https://discord.com/channels/1302588750630621184/1399202526070308976	t	f	t	2025-08-04 18:45:16.987116+00
4	Kingdra	Swift Swim	Modest	uu	https://discord.com/channels/1302588750630621184/1399201738724212808	f	f	f	2025-08-04 18:43:55.832426+00
1	Slowking-Galar	Regenerator	Sassy	ou	https://discord.com/channels/1302588750630621184/1399200070439800854	f	f	f	2025-08-04 18:39:13.524884+00
3	Alomomola	Regenerator	Relaxed	ou	https://discord.com/channels/1302588750630621184/1399200854619193364	f	f	f	2025-08-04 18:42:51.434982+00
7	Ceruledge	Weak Armor	Adamant	ou	https://discord.com/channels/1302588750630621184/1399203649300987974	f	f	f	2025-08-04 18:46:34.149021+00
10	Pelipper	Drizzle	Bold	ou	https://discord.com/channels/1302588750630621184/1399266879725637632	f	f	f	2025-08-04 18:50:12.785001+00
17	Barraskewda	Swift Swim	Adamant	ou	https://discord.com/channels/1302588750630621184/1399597038357844120	f	f	f	2025-08-04 18:58:42.386483+00
24	Corviknight	Pressure	Impish	ou	https://discord.com/channels/1302588750630621184/1400181182410526841	f	f	f	2025-08-04 19:05:03.130401+00
26	Great Tusk	Protosynthesis	Jolly	ou	https://discord.com/channels/1302588750630621184/1399199801291309136	f	f	f	2025-08-04 19:06:44.828108+00
27	Xurkitree	Beast Boost	Timid	uu	https://discord.com/channels/1302588750630621184/1405011627312545913	f	f	f	2025-08-13 02:16:01.49589+00
28	Arctozolt	Slush Rush	Naive	ou	https://discord.com/channels/1302588750630621184/1405012301819412601	f	f	f	2025-08-13 02:18:15.767131+00
29	Roaring Moon	Protosynthesis	Jolly	ou	https://discord.com/channels/1302588750630621184/1405261671374520472	f	f	f	2025-08-13 18:49:13.947565+00
30	Zapdos-Galar	Defiant	Jolly	uu	https://discord.com/channels/1302588750630621184/1415383096806871100	f	f	f	2025-09-10 17:12:21.40187+00
\.


--
-- Data for Name: tournament_matches; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.tournament_matches (id, tournament_id, participant1_id, participant2_id, challonge_id, round, completed, winner_participant_id, score) FROM stdin;
\.


--
-- Data for Name: tournament_participants; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.tournament_participants (tournament_id, user_id, challonge_id, id) FROM stdin;
1	13	274469005	2
1	15	274473650	3
1	16	274506816	4
1	17	274507297	5
1	18	274507866	6
1	19	274511293	7
1	20	274514532	8
1	1	274518086	10
1	10	274557766	12
1	11	274564080	13
1	21	274574459	14
\.


--
-- Data for Name: tournaments; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.tournaments (id, challonge_id, name, slug, url, ongoing, winner_id, current_tournament) FROM stdin;
1	16903851	AFC Blaze Cup	afc_blaze_cup	https://challonge.com/afc_blaze_cup	f	\N	t
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: afc_squad
--

COPY public.users (id, discord_id, username, country_timezone, is_active, created_at, pvp_experience) FROM stdin;
2	1407815102454960201	xiyou	China	t	2025-08-21 12:16:21.82665+00	novice
3	487615845951078414	iZandex	Spain	t	2025-08-27 18:30:07.65925+00	novice
4	205722519208984576	ImLeamox	Germany	t	2025-08-30 11:04:53.514964+00	novice
5	319455756699041792	Raehl	Brazil	t	2025-09-08 12:49:56.200869+00	novice
6	725375834202046496	Vysa	Germany	t	2025-09-08 14:49:08.445261+00	novice
7	350825970783092766	ItachiUchiha	Brazil	t	2025-09-17 09:32:10.898589+00	novice
8	277444924633251840	aFasiagr	Greece	t	2025-09-17 17:39:22.661753+00	novice
1	195599180624822272	Adinho	Netherlands	t	2025-08-04 19:07:30.307698+00	Veteran
9	358171445286928385	Ape_Gang	viena	t	2025-09-20 04:04:14.224319+00	veteran
10	242376879791669248	starmaker	India	t	2025-09-20 17:31:55.778444+00	novice
11	462539045361418241	EXP2ME	New Zealand	t	2025-09-26 20:44:59.821894+00	intermediate
12	1328657649570545725	Babykarrot	Philippines	t	2025-09-26 23:58:28.610069+00	veteran
13	1402024910309818422	Killernacho	Netherlands	t	2025-10-03 08:41:30.513456+00	intermediate
14	212600510920785920	Jazukia	Netherlands	t	2025-10-03 09:01:42.494631+00	novice
15	204972425186770944	RSequeira10	portugal	t	2025-10-03 10:03:47.787368+00	veteran
16	853400980900151327	BeazyTV	United States	t	2025-10-03 16:45:03.543209+00	intermediate
17	225252203592417281	Reilith	Portugal	t	2025-10-03 16:54:33.656639+00	intermediate
18	310485123156148225	Florian1	Austria	t	2025-10-03 17:01:17.854048+00	veteran
19	920778639363166228	Alucir	Brazil	t	2025-10-03 17:47:37.558282+00	novice
20	468936156642410496	Igfer	Pery	t	2025-10-03 18:15:37.958969+00	intermediate
21	376079758498463754	pawol	Poland	t	2025-05-07 00:00:00+00	veteran
\.


--
--

SELECT pg_catalog.setval('public.loans_id_seq', 1, false);


--
--

SELECT pg_catalog.setval('public.pokemon_id_seq', 33, true);


--
--

SELECT pg_catalog.setval('public.tournament_matches_id_seq', 1, false);


--
--

SELECT pg_catalog.setval('public.tournament_participants_id_seq', 14, true);


--
--

SELECT pg_catalog.setval('public.tournaments_id_seq', 1, true);


--
--

SELECT pg_catalog.setval('public.users_id_seq', 21, true);


--
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_pkey PRIMARY KEY (id);


--
--

ALTER TABLE ONLY public.tournament_participants
    ADD CONSTRAINT pk_tournament_participants PRIMARY KEY (id);


--
--

ALTER TABLE ONLY public.pokemon
    ADD CONSTRAINT pokemon_pkey PRIMARY KEY (id);


--
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_pkey PRIMARY KEY (id);


--
--

ALTER TABLE ONLY public.tournaments
    ADD CONSTRAINT tournaments_pkey PRIMARY KEY (id);


--
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT uq_tm_t_chid UNIQUE (tournament_id, challonge_id);


--
--

ALTER TABLE ONLY public.tournament_participants
    ADD CONSTRAINT uq_tp_tournament_chid UNIQUE (tournament_id, challonge_id);


--
--

ALTER TABLE ONLY public.tournament_participants
    ADD CONSTRAINT uq_tp_tournament_user UNIQUE (tournament_id, user_id);


--
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_discord_id_key UNIQUE (discord_id);


--
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_pokemon_id_fkey FOREIGN KEY (pokemon_id) REFERENCES public.pokemon(id);


--
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_participant1_id_fkey FOREIGN KEY (participant1_id) REFERENCES public.tournament_participants(id) ON DELETE SET NULL;


--
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_participant2_id_fkey FOREIGN KEY (participant2_id) REFERENCES public.tournament_participants(id) ON DELETE SET NULL;


--
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_tournament_id_fkey FOREIGN KEY (tournament_id) REFERENCES public.tournaments(id) ON DELETE CASCADE;


--
--

ALTER TABLE ONLY public.tournament_matches
    ADD CONSTRAINT tournament_matches_winner_participant_id_fkey FOREIGN KEY (winner_participant_id) REFERENCES public.tournament_participants(id) ON DELETE SET NULL;


--
--

ALTER TABLE ONLY public.tournament_participants
    ADD CONSTRAINT tournament_participants_tournament_id_fkey FOREIGN KEY (tournament_id) REFERENCES public.tournaments(id) ON DELETE CASCADE;


--
--

ALTER TABLE ONLY public.tournament_participants
    ADD CONSTRAINT tournament_participants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
--

ALTER TABLE ONLY public.tournaments
    ADD CONSTRAINT tournaments_winner_id_fkey FOREIGN KEY (winner_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

