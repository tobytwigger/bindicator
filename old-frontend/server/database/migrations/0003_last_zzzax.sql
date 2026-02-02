CREATE TABLE `bins` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`council_name` text NOT NULL,
	`name` text NOT NULL,
	`home_id` integer NOT NULL,
	FOREIGN KEY (`home_id`) REFERENCES `homes`(`id`) ON UPDATE no action ON DELETE no action
);
