PRAGMA foreign_keys=OFF;--> statement-breakpoint
CREATE TABLE `__new_homes` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`name` text NOT NULL,
	`council` text,
	`council_data` text,
	`active` integer DEFAULT false NOT NULL
);
--> statement-breakpoint
INSERT INTO `__new_homes`("id", "name", "council", "council_data", "active") SELECT "id", "name", "council", "council_data", "active" FROM `homes`;--> statement-breakpoint
DROP TABLE `homes`;--> statement-breakpoint
ALTER TABLE `__new_homes` RENAME TO `homes`;--> statement-breakpoint
PRAGMA foreign_keys=ON;--> statement-breakpoint
CREATE UNIQUE INDEX `homes_name_unique` ON `homes` (`name`);