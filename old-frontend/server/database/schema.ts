import {sqliteTable, text, integer, unique} from 'drizzle-orm/sqlite-core'

export const homes = sqliteTable('homes', {
    id: integer('id').primaryKey({ autoIncrement: true }),
    name: text('name').notNull().unique(),
    council: text('council'),
    council_data: text('council_data', {mode: 'json'}),
    active: integer('active', {mode: 'boolean'}).notNull().default(false),
    timeout: integer('timeout').notNull().default(180),
    put_out_day_before: integer('put_out_day_before', {mode: 'boolean'}).notNull().default(false),
})

export const bins = sqliteTable('bins', {
    id: integer('id').primaryKey({ autoIncrement: true }),
    council_name: text('council_name').notNull(),
    name: text('name').notNull(),
    position: integer('position').notNull(),
    home_id: integer('home_id').notNull().references(() => homes.id),
}, (t) => ({
    unq: unique().on(t.position, t.home_id)
}));

export const schedules = sqliteTable('schedules', {
    id: integer('id').primaryKey({ autoIncrement: true }),
    start: text('start', {mode: 'timestamp'}).notNull(),
    end: text('end', {mode: 'timestamp'}),
    repeat_weeks: integer('repeat').notNull(),
    home_id: integer('home_id').notNull().references(() => homes.id),
});

export const bin_schedules = sqliteTable('bin_schedules', {
    id: integer('id').primaryKey({ autoIncrement: true }),
    bin_id: integer('bin_id').notNull().references(() => bins.id),
    schedule_id: integer('schedule_id').notNull().references(() => schedules.id),
});

export const bin_days = sqliteTable('bin_days', {
    id: integer('id').primaryKey({ autoIncrement: true }),
    bin_id: integer('bin_id').notNull().references(() => bins.id),
    date: text('date', {mode: 'timestamp'}).notNull(),
    home_id: integer('home_id').notNull().references(() => homes.id),
    schedule_id: integer('schedule_id').references(() => schedules.id),
    put_out_at: text('put_out_at', {mode: 'timestamp'}),
});

export const bin_day_replacements = sqliteTable('bin_day_replacements', {
    id: integer('id').primaryKey({ autoIncrement: true }),
    replace: text('replace', {mode: 'timestamp'}),
    with: text('with', {mode: 'timestamp'}).notNull(),
    home_id: integer('home_id').notNull().references(() => homes.id),
});