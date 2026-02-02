import { drizzle } from 'drizzle-orm/libsql'
export { sql, eq, and, or } from 'drizzle-orm'
import path from 'path'
import * as schema from '../database/schema'

export const tables = schema

const shouldLog = false

export function useDrizzle() {
    return drizzle('file:/home/toby/database.sqlite', { schema, logger: shouldLog })
}

export type Home = typeof schema.homes.$inferSelect

export type Bin = typeof schema.bins.$inferSelect

export type Schedule = typeof schema.schedules.$inferSelect

export type BinSchedule = typeof schema.bin_schedules.$inferSelect

export type BinDay = typeof schema.bin_days.$inferSelect

export type BinDayReplacement = typeof schema.bin_day_replacements.$inferSelect