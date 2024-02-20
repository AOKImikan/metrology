#!/usr/bin/env python3
import os

def count_lines(directory, extensions):
    total_lines = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(extensions)):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += sum(1 for line in f)
    return total_lines

directory_path = './modules'
file_extensions = ['.py']

total_lines = count_lines(directory_path, file_extensions)
print(f'Total lines: {total_lines}')
