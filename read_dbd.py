from os.path import splitext


def read_dbd(filepath: str) -> dict:
    '''
    读取.dbd文件，返回一个字典。
    字典中的数据都是用字符串形式存储的。
    '''
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