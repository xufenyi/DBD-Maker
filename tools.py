from os.path import splitext


def read_dbd(filepath: str) -> dict:
    """
    读取.dbd文件，返回一个字典。
    字典中的数据都是用字符串形式存储的。
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = []
        for line in f:
            if line.strip():
                lines.append(line.strip())
    result = {}
    movements = []
    for line in lines:
        if line.startswith('File:'):
            result['File'] = splitext(line[5:].strip())[0]
        elif line.startswith('Unit:'):
            result['Unit'] = line[5:].strip()
        elif line.startswith('LaserOnDelay'):
            result['LaserOnDelay'] = line[12:].strip()
        elif line.startswith('LaserOffDelay'):
            result['LaserOffDelay'] = line[13:].strip()
        elif line.startswith('JumpSpeed'):
            result['JumpSpeed'] = line[10:].strip()
        elif line.startswith('MarkSpeed'):
            result['MarkSpeed'] = line[10:].strip()
        elif line.startswith('JumpDelay'):
            result['JumpDelay'] = line[10:].strip()
        elif line.startswith('MarkDelay'):
            result['MarkDelay'] = line[10:].strip()
        elif line.startswith('StepPeriod'):
            result['StepPeriod'] = line[11:].strip()
        elif line.startswith('jump_abs') or line.startswith('mark_abs'):
            action, x, y = line.split(' ')
            action = action[:4]
            movements.append((x.strip(), y.strip(), action.strip()))
            
    result['Movements'] = movements
    return result


def is_valid_csv_line(line: str) -> bool:
    """
    检查一行数据是否有效。
    有效的行应该包含三个部分：x坐标、y坐标和动作，它们用逗号分隔。
    """
    parts = line.strip().split(',')
    if len(parts) != 3:
        return False
    x, y, action = parts
    return x.strip().isdigit() and y.strip().isdigit() and action.strip() in ('mark', 'jump')


def read_csv(filepath: str) -> list:
    """
    读取.csv文件，返回一个列表。
    列表的元素是元组，每个元组包含x、y坐标和动作。
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = []
        for line in f:
            if is_valid_csv_line(line):
                x, y, action = line.strip().split(',')
                lines.append((x.strip(), y.strip(), action.strip()))
    return lines


def write_csv_example(filepath: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('x,y,action\n')
        f.write('10,20,jump\n')
        f.write('30,40,mark')
