import {PythonShell} from 'python-shell';
import path from 'path';

export async function testHome(homeId: string): Promise<{ valid: boolean, error?: string|undefined }> {
    return await runPython('test-home', [homeId]);
}

export async function getBinOptions(homeId: string): Promise<{ options: string[] }> {
    return await runPython('get-bin-options', [homeId]);
}

async function runPython(subcommand: string, args: string[]) {
    let root = process.env.NODE_ENV === 'development' ? './../python/' : '/home/toby/when-is-bins/python/';
    let messages = await PythonShell.run('api.py', {
        mode: 'text',
        pythonPath: root + '.venv/bin/python',
        pythonOptions: ['-u'],
        scriptPath: root + 'src',
        args: [subcommand, ...args]
    });

    if (messages.length > 1) {
        throw new Error('Too many print lines in python');
    }
    if (messages.length === 0) {
        throw new Error('No print lines in python');
    }

    return JSON.parse(messages[0]);
}