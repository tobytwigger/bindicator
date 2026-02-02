PRAGMA foreign_keys=OFF;--> statement-breakpoint
CREATE TABLE `__new_bin_day_replacements` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`replace` text,
	`with` text NOT NULL,
	`home_id` integer NOT NULL,
	FOREIGN KEY (`home_id`) REFERENCES `homes`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
INSERT INTO `__new_bin_day_replacements`("id", "replace", "with", "home_id") SELECT "id", "replace", "with", "home_id" FROM `bin_day_replacements`;--> statement-breakpoint
DROP TABLE `bin_day_replacements`;--> statement-breakpoint
ALTER TABLE `__new_bin_day_replacements` RENAME TO `bin_day_replacements`;--> statement-breakpoint
PRAGMA foreign_keys=ON;