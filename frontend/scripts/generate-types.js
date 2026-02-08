import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFile, mkdir } from 'fs/promises';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const execAsync = promisify(exec);
const __dirname = dirname(fileURLToPath(import.meta.url));

async function generateTypes() {
  try {
    const apiUrl = process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000';
    const openapiUrl = `${apiUrl}/openapi.json`;

    console.log(`Fetching OpenAPI schema from ${openapiUrl}...`);

    // Fetch the OpenAPI schema
    const response = await fetch(openapiUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch OpenAPI schema: ${response.statusText}`);
    }

    const schema = await response.text();

    // Write schema to temp file
    const tempSchemaPath = `${__dirname}/../.temp-openapi.json`;
    await writeFile(tempSchemaPath, schema);

    console.log('Generating TypeScript types...');

    // Generate TypeScript types
    const outputPath = `${__dirname}/../types/api.ts`;
    await mkdir(dirname(outputPath), { recursive: true });

    await execAsync(`npx openapi-typescript ${tempSchemaPath} -o ${outputPath}`);

    console.log('✅ TypeScript types generated successfully!');

    // Clean up temp file
    await execAsync(`rm ${tempSchemaPath}`);
  } catch (error) {
    console.error('❌ Error generating types:', error.message);
    process.exit(1);
  }
}

generateTypes();
