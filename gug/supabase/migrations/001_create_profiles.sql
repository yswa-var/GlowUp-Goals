-- Create users table to extend auth.users with custom attributes
create table users (
  -- Primary key that references Supabase auth.users
  id uuid references auth.users on delete cascade primary key,
  
  -- Custom attributes for ADHD-focused app
  brain_type text check (brain_type in ('hyperfocus', 'scattered')),
  sensory_sensitivity integer check (sensory_sensitivity >= 1 and sensory_sensitivity <= 5),
  
  -- Timestamps
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create goals table
create table goals (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  long_term text not null,
  weekly_focus text not null,
  why_matters text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create tasks table
create table tasks (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  goal_id uuid references goals on delete cascade not null,
  title text not null,
  why text not null,
  status text default 'pending' check (status in ('pending', 'in_progress', 'completed', 'blocked')),
  time_estimate integer, -- in minutes
  blocker_emoji text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create therapeutic_scripts table (PRE-APPROVED CONTENT ONLY)
create table therapeutic_scripts (
  id uuid default gen_random_uuid() primary key,
  trigger text not null,
  title text not null,
  actions jsonb not null, -- array of action strings
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table users enable row level security;
alter table goals enable row level security;
alter table tasks enable row level security;
alter table therapeutic_scripts enable row level security;

-- RLS Policies for users
create policy "Users can view their own profile" 
  on users for select 
  using (auth.uid() = id);

create policy "Users can insert their own profile" 
  on users for insert 
  with check (auth.uid() = id);

create policy "Users can update their own profile" 
  on users for update 
  using (auth.uid() = id);

-- RLS Policies for goals
create policy "Users can view their own goals" 
  on goals for select 
  using (auth.uid() = user_id);

create policy "Users can insert their own goals" 
  on goals for insert 
  with check (auth.uid() = user_id);

create policy "Users can update their own goals" 
  on goals for update 
  using (auth.uid() = user_id);

create policy "Users can delete their own goals" 
  on goals for delete 
  using (auth.uid() = user_id);

-- RLS Policies for tasks
create policy "Users can view their own tasks" 
  on tasks for select 
  using (auth.uid() = user_id);

create policy "Users can insert their own tasks" 
  on tasks for insert 
  with check (auth.uid() = user_id);

create policy "Users can update their own tasks" 
  on tasks for update 
  using (auth.uid() = user_id);

create policy "Users can delete their own tasks" 
  on tasks for delete 
  using (auth.uid() = user_id);

-- RLS Policies for therapeutic_scripts (public read-only)
create policy "Anyone can view therapeutic scripts" 
  on therapeutic_scripts for select 
  using (true);

-- Create updated_at trigger function
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$ language plpgsql;

-- Create triggers for updated_at
create trigger update_users_updated_at
  before update on users
  for each row
  execute function update_updated_at_column();

create trigger update_tasks_updated_at
  before update on tasks
  for each row
  execute function update_updated_at_column();

-- Function to handle new user registration
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id)
  values (new.id);
  return new;
end;
$$ language plpgsql security definer;

-- Trigger to automatically create user profile on signup
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Seed therapeutic_scripts with initial content
insert into therapeutic_scripts (trigger, title, actions) values
  ('🤯', 'Overwhelmed?', '["Delete 1 task → restart", "Set 2-min timer"]');