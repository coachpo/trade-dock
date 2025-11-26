create table public.longbridge_trading
(
    datetime          timestamp,
    ticker            varchar,
    interval          varchar(3),
    position          integer,
    ta_recommendation varchar,
    yf_signal         varchar,
    price_close       double precision,
    email             varchar,
    direction         varchar,
    order_id          varchar,
    handling_fee      double precision,
    price_cost        double precision,
    price_potential   double precision
);

comment on column public.longbridge_trading.datetime is 'New York';

alter table public.longbridge_trading
    owner to lightwing;

create table public.notification_email
(
    id                    varchar(18) default nextval('notification_email_id_seq'::regclass) not null
        primary key,
    ticker                varchar(16)                                                        not null,
    signal                varchar(16)                                                        not null,
    last_updated_datetime timestamp                                                          not null,
    last_price            numeric(10, 2)                                                     not null
        constraint notification_email_last_price_check
            check (last_price >= (0)::numeric),
    interval              varchar(3),
    creation_time         timestamp
);

comment on column public.notification_email.creation_time is 'EST';

alter table public.notification_email
    owner to lightwing;

create table public.tradingview_analysis
(
    ticker                     text,
    datetime                   timestamp,
    interval                   text,
    "Recommend.Other"          numeric,
    "Recommend.All"            numeric,
    "Recommend.MA"             numeric,
    "RSI"                      numeric,
    "RSI[1]"                   numeric,
    "Stoch.K"                  numeric,
    "Stoch.D"                  numeric,
    "Stoch.K[1]"               numeric,
    "Stoch.D[1]"               numeric,
    "CCI20"                    numeric,
    "CCI20[1]"                 numeric,
    "ADX"                      numeric,
    "ADX+DI"                   numeric,
    "ADX-DI"                   numeric,
    "ADX+DI[1]"                numeric,
    "ADX-DI[1]"                numeric,
    "AO"                       numeric,
    "AO[1]"                    numeric,
    "Mom"                      numeric,
    "Mom[1]"                   numeric,
    "MACD.macd"                numeric,
    "MACD.signal"              numeric,
    "Rec.Stoch.RSI"            integer,
    "Stoch.RSI.K"              numeric,
    "Rec.WR"                   integer,
    "W.R"                      numeric,
    "Rec.BBPower"              integer,
    "BBPower"                  numeric,
    "Rec.UO"                   integer,
    "UO"                       numeric,
    close                      numeric,
    "EMA5"                     numeric,
    "SMA5"                     numeric,
    "EMA10"                    numeric,
    "SMA10"                    numeric,
    "EMA20"                    numeric,
    "SMA20"                    numeric,
    "EMA30"                    numeric,
    "SMA30"                    numeric,
    "EMA50"                    numeric,
    "SMA50"                    numeric,
    "EMA100"                   numeric,
    "SMA100"                   numeric,
    "EMA200"                   numeric,
    "SMA200"                   numeric,
    "Rec.Ichimoku"             numeric,
    "Ichimoku.BLine"           numeric,
    "Rec.VWMA"                 numeric,
    "VWMA"                     numeric,
    "Rec.HullMA9"              numeric,
    "HullMA9"                  numeric,
    "Pivot.M.Classic.S3"       numeric,
    "Pivot.M.Classic.S2"       numeric,
    "Pivot.M.Classic.S1"       numeric,
    "Pivot.M.Classic.Middle"   numeric,
    "Pivot.M.Classic.R1"       numeric,
    "Pivot.M.Classic.R2"       numeric,
    "Pivot.M.Classic.R3"       numeric,
    "Pivot.M.Fibonacci.S3"     numeric,
    "Pivot.M.Fibonacci.S2"     numeric,
    "Pivot.M.Fibonacci.S1"     numeric,
    "Pivot.M.Fibonacci.Middle" numeric,
    "Pivot.M.Fibonacci.R1"     numeric,
    "Pivot.M.Fibonacci.R2"     numeric,
    "Pivot.M.Fibonacci.R3"     numeric,
    "Pivot.M.Camarilla.S3"     numeric,
    "Pivot.M.Camarilla.S2"     numeric,
    "Pivot.M.Camarilla.S1"     numeric,
    "Pivot.M.Camarilla.Middle" numeric,
    "Pivot.M.Camarilla.R1"     numeric,
    "Pivot.M.Camarilla.R2"     numeric,
    "Pivot.M.Camarilla.R3"     numeric,
    "Pivot.M.Woodie.S3"        numeric,
    "Pivot.M.Woodie.S2"        numeric,
    "Pivot.M.Woodie.S1"        numeric,
    "Pivot.M.Woodie.Middle"    numeric,
    "Pivot.M.Woodie.R1"        numeric,
    "Pivot.M.Woodie.R2"        numeric,
    "Pivot.M.Woodie.R3"        numeric,
    "Pivot.M.Demark.S1"        numeric,
    "Pivot.M.Demark.Middle"    numeric,
    "Pivot.M.Demark.R1"        numeric,
    open                       numeric,
    "P.SAR"                    numeric,
    "BB.lower"                 numeric,
    "BB.upper"                 numeric,
    "AO[2]"                    numeric,
    volume                     numeric,
    change                     numeric,
    low                        numeric,
    high                       numeric
);

comment on column public.tradingview_analysis.datetime is 'HKT';

alter table public.tradingview_analysis
    owner to lightwing;

create table public.yahoo_finance_data
(
    ticker      varchar(20),
    "Datetime"  timestamp,
    "Interval"  varchar(6),
    "Open"      double precision,
    "High"      double precision,
    "Low"       double precision,
    "Close"     double precision,
    "Adj Close" double precision,
    "Volume"    bigint,
    "BuyIndex"  varchar(20)
);

comment on column public.yahoo_finance_data."Datetime" is 'NYT';

alter table public.yahoo_finance_data
    owner to lightwing;

