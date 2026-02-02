CREATE TABLE `bin_days` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`bin_id` integer NOT NULL,
	`date` integer NOT NULL,
	`home_id` integer NOT NULL,
	`schedule_id` integer,
	FOREIGN KEY (`bin_id`) REFERENCES `bins`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`home_id`) REFERENCES `homes`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`schedule_id`) REFERENCES `schedules`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `bin_schedules` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`bin_id` integer NOT NULL,
	`schedule_id` integer NOT NULL,
	FOREIGN KEY (`bin_id`) REFERENCES `bins`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`schedule_id`) REFERENCES `schedules`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `schedules` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`start` integer NOT NULL,
	`end` integer,
	`repeat` integer NOT NULL,
	`home_id` integer NOT NULL,
	FOREIGN KEY (`home_id`) REFERENCES `homes`(`id`) ON UPDATE no action ON DELETE no action
);
