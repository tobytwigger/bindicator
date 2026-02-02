PRAGMA foreign_keys=OFF;--> statement-breakpoint
CREATE TABLE `__new_bin_days` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`bin_id` integer NOT NULL,
	`date` text NOT NULL,
	`home_id` integer NOT NULL,
	`schedule_id` integer,
	FOREIGN KEY (`bin_id`) REFERENCES `bins`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`home_id`) REFERENCES `homes`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`schedule_id`) REFERENCES `schedules`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
INSERT INTO `__new_bin_days`("id", "bin_id", "date", "home_id", "schedule_id") SELECT "id", "bin_id", "date", "home_id", "schedule_id" FROM `bin_days`;--> statement-breakpoint
DROP TABLE `bin_days`;--> statement-breakpoint
ALTER TABLE `__new_bin_days` RENAME TO `bin_days`;--> statement-breakpoint
PRAGMA foreign_keys=ON;--> statement-breakpoint
CREATE TABLE `__new_schedules` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`start` text NOT NULL,
	`end` text,
	`repeat` integer NOT NULL,
	`home_id` integer NOT NULL,
	FOREIGN KEY (`home_id`) REFERENCES `homes`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
INSERT INTO `__new_schedules`("id", "start", "end", "repeat", "home_id") SELECT "id", "start", "end", "repeat", "home_id" FROM `schedules`;--> statement-breakpoint
DROP TABLE `schedules`;--> statement-breakpoint
ALTER TABLE `__new_schedules` RENAME TO `schedules`;