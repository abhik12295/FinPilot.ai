-- =========================================
-- EXTENSION
-- =========================================
create extension if not exists "pgcrypto";

-- =========================================
-- ACCOUNTS
-- =========================================
create table if not exists accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  simplefin_account_id text not null,
  name text not null,
  type text,
  balance numeric(14,2) default 0,
  currency text default 'USD',
  updated_at timestamptz default now(),
  created_at timestamptz default now(),

  constraint unique_user_simplefin_account 
  unique (user_id, simplefin_account_id)
);

-- =========================================
-- TRANSACTIONS
-- =========================================
create table if not exists transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  account_id uuid references accounts(id) on delete cascade,
  simplefin_transaction_id text not null,
  date date not null,
  description text,
  merchant text,
  amount numeric(14,2) not null,
  category text default 'Uncategorized',
  pending boolean default false,
  raw_data jsonb,
  created_at timestamptz default now(),

  constraint unique_user_simplefin_transaction 
  unique (user_id, simplefin_transaction_id)
);

-- =========================================
-- BUDGETS
-- =========================================
create table if not exists budgets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null,
  monthly_limit numeric(14,2) not null,
  created_at timestamptz default now(),

  constraint unique_user_budget_category 
  unique (user_id, category)
);

-- =========================================
-- SUBSCRIPTIONS
-- =========================================
create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  merchant text not null,
  amount numeric(14,2),
  frequency text default 'monthly',
  last_seen date,
  status text default 'active',
  created_at timestamptz default now(),

  constraint unique_user_subscription_merchant 
  unique (user_id, merchant)
);

-- =========================================
-- RECOMMENDATIONS
-- =========================================
create table if not exists recommendations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  type text not null,
  title text not null,
  message text not null,
  priority text default 'medium',
  status text default 'open',
  created_at timestamptz default now()
);

-- =========================================
-- AI INSIGHTS
-- =========================================
create table if not exists ai_insights (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  summary text not null,
  insight_type text default 'daily_summary',
  created_at timestamptz default now()
);

-- =========================================
-- INDEXES (Performance)
-- =========================================
create index if not exists idx_accounts_user_id on accounts(user_id);

create index if not exists idx_transactions_user_id on transactions(user_id);
create index if not exists idx_transactions_account_id on transactions(account_id);
create index if not exists idx_transactions_date on transactions(date);
create index if not exists idx_transactions_category on transactions(category);

create index if not exists idx_budgets_user_id on budgets(user_id);
create index if not exists idx_subscriptions_user_id on subscriptions(user_id);
create index if not exists idx_recommendations_user_id on recommendations(user_id);
create index if not exists idx_ai_insights_user_id on ai_insights(user_id);

-- =========================================
-- ENABLE RLS
-- =========================================
alter table accounts enable row level security;
alter table transactions enable row level security;
alter table budgets enable row level security;
alter table subscriptions enable row level security;
alter table recommendations enable row level security;
alter table ai_insights enable row level security;

-- =========================================
-- FINAL PRODUCTION POLICIES
-- =========================================

create policy "accounts_policy"
on accounts
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "transactions_policy"
on transactions
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "budgets_policy"
on budgets
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "subscriptions_policy"
on subscriptions
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "recommendations_policy"
on recommendations
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "ai_insights_policy"
on ai_insights
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);