import { migrate } from 'drizzle-orm/libsql/migrator'

export default defineNitroPlugin(async (nitroApp) => {
    const db = useDrizzle();
    	try {
			let migrationsFolder = process.env.NODE_ENV === 'development'
				? 'server/database/migrations'
				: '/home/toby/when-is-bins/js/server/database/migrations'
		await migrate(db, { migrationsFolder: migrationsFolder })
		console.log('Migration completed ✅')
	} catch (error) {
		console.error('Migration failed 🚨:', error)
	}
})