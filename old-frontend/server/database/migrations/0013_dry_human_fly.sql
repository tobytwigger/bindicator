ALTER TABLE `bin_days` ADD `put_out_at` text;--> statement-breakpoint
ALTER TABLE `homes` ADD `put_out_at` text DEFAULT 'day_before';