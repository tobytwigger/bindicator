CREATE TABLE `homes` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`name` text NOT NULL,
	`council` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `homes_name_unique` ON `homes` (`name`);