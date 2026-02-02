CREATE TABLE `holiday_schedule` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`replace` text NOT NULL,
	`with` text NOT NULL,
	`home_id` integer NOT NULL,
	FOREIGN KEY (`home_id`) REFERENCES `homes`(`id`) ON UPDATE no action ON DELETE no action
);
