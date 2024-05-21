from fs_classes import *


def print_error(message):
    print('\033[91m' + message + '\033[0m')


def print_ok(message):
    print('\033[92m' + message + '\033[0m')


def print_descriptor_header():
    print('%10s  %10s  %10s  %10s  %10s  %s' % ('№', 'type', 'links', 'length', 'blocks', 'name'))


def check_fs():
    if infoStatic.FS is None:
        print_error('The file system is not initialised!')
        return 1
    return 0


def fs_mkfs(n):
    if infoStatic.FS is not None:
        print_error('The file system was already been initialised!')
        return
    if not type(n) is int:
        print_error('Type should be int!')
        return
    infoStatic.FS = FS(n)
    print_ok('File system is initialised!')


def fs_stat(name):
    if check_fs():
        return
    for descriptor in infoStatic.FS.descriptors:
        if descriptor.name == name:
            print_descriptor_header()
            descriptor.show_info()
            return
    print_error(f'There is no file with this name: {name}')


def fs_ls():
    if check_fs():
        return
    print_descriptor_header()
    for descriptor in infoStatic.FS.descriptors:
        descriptor.show_info()


def fs_create(name):
    if check_fs():
        return
    if len(str(name)) > infoStatic.MAX_FILE_NAME_LENGTH:
        print_error(f'File name is too large. should be less then {infoStatic.MAX_FILE_NAME_LENGTH}')
    if infoStatic.FS.descriptors_num >= infoStatic.FS.descriptors_max_num:
        print_error('All descriptors were used!')
        return
    for descriptor in infoStatic.FS.descriptors:
        if descriptor.name == name:
            print_error('File with this name exist!');
            return
    descriptor_num = None
    for i, value in enumerate(infoStatic.FS.descriptorsBitmap):
        if not value:
            infoStatic.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    descriptor = Desc(descriptor_num, 'regular', 0, name)
    infoStatic.FS.descriptors.append(descriptor)
    infoStatic.FS.descriptors_num += 1
    print_descriptor_header()
    descriptor.show_info()


def fs_link(name1, name2):
    if check_fs():
        return
    if len(str(name2)) > infoStatic.MAX_FILE_NAME_LENGTH:
        print_error(f'File name is too large. should be less then {infoStatic.MAX_FILE_NAME_LENGTH}')
    for descriptor in infoStatic.FS.descriptors:
        if descriptor.name == name2:
            print_error(f'An instance with this name was already created! {name2}')
            return
    for descriptor in infoStatic.FS.descriptors:
        if descriptor.name == name1:
            new_link = Link(descriptor, name2)
            descriptor.links.append(new_link)
            infoStatic.FS.descriptors.append(new_link)
            print_descriptor_header()
            new_link.show_info()
            return
    print_error(f'There is no file with name {name1}')


def fs_unlink(name):
    if check_fs():
        return
    for descriptor in infoStatic.FS.descriptors:
        if descriptor.name == name:
            if isinstance(descriptor, Desc):
                print_error(f'There is no link with name {name}. It is a file!')
                return
            else:
                descriptor.descriptor.links_num -= 1
                infoStatic.FS.descriptors.remove(descriptor)
                print_ok('Unlinked!')
                return
    print_error(f'There is no link with name {name}')


def fs_open(name):
    if check_fs():
        return
    for descriptor in infoStatic.FS.descriptors:
        if descriptor.name == name:
            openedFile = FileDesc(descriptor)
            infoStatic.FS.opened_files.append(openedFile)
            print_ok(f'File {name} is opened with id {openedFile.num_descriptor}!')
            return
    print_error(f'There is no file with name {name}')


def fs_close(fd):
    if check_fs():
        return
    if fd in infoStatic.FS.opened_files_num_descriptors:
        infoStatic.FS.opened_files_num_descriptors.remove(fd)
        for openedFile in infoStatic.FS.opened_files:
            if openedFile.num_descriptor == fd:
                infoStatic.FS.opened_files.remove(openedFile)
                del openedFile
                print_ok(f'File with id {fd} is closed!')
                return
    print_error(f'There is no file opened with ID = {fd}')


def fs_seek(fd, offset):
    if check_fs():
        return
    if fd not in infoStatic.FS.opened_files_num_descriptors:
        print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in infoStatic.FS.opened_files:
        if openedFile.num_descriptor == fd:
            openedFile.offset = offset
            print_ok('Offset was set!')
            return


def fs_write(fd, size, val):
    if check_fs():
        return
    if len(str(val)) != 1:
        print_error('Val should be 1 byte size!')
        return
    if fd not in infoStatic.FS.opened_files_num_descriptors:
        print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in infoStatic.FS.opened_files:
        if openedFile.num_descriptor == fd:
            num = len(openedFile.descriptor.blocks)
            while openedFile.offset + size > num * infoStatic.BLOCK_SIZE:
                openedFile.descriptor.blocks.append(['\0' for i in range(infoStatic.BLOCK_SIZE)])
                num += 1
            num = 0
            for i in range(openedFile.offset + size):
                if i == infoStatic.BLOCK_SIZE * num + infoStatic.BLOCK_SIZE:
                    num += 1
                if i >= openedFile.offset:
                    openedFile.descriptor.blocks[num][i - num * infoStatic.BLOCK_SIZE] = val
            if openedFile.descriptor.length < openedFile.offset + size:
                openedFile.descriptor.length = openedFile.offset + size
            print_ok('Data were written to file!')
            return


def fs_read(fd, size):
    if check_fs():
        return
    if fd not in infoStatic.FS.opened_files_num_descriptors:
        print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in infoStatic.FS.opened_files:
        if openedFile.num_descriptor == fd:
            if openedFile.descriptor.length < openedFile.offset + size:
                print_error(
                    f'File length is {openedFile.descriptor.length}. We can\'t read from {openedFile.offset} to {openedFile.offset + size}')
                return
            num = openedFile.offset // infoStatic.BLOCK_SIZE
            answer = ""
            for i in range(openedFile.offset, openedFile.offset + size):
                if i == infoStatic.BLOCK_SIZE * num + infoStatic.BLOCK_SIZE:
                    num += 1
                answer += str(openedFile.descriptor.blocks[num][i - num * infoStatic.BLOCK_SIZE])
            print(answer)


def fs_truncate(name, size):
    if check_fs():
        return
    for descriptor in infoStatic.FS.descriptors:
        if descriptor.name == name:
            if size < descriptor.length:
                num = len(descriptor.blocks)
                while num * infoStatic.BLOCK_SIZE > size + infoStatic.BLOCK_SIZE:
                    descriptor.blocks.pop(num - 1)
                    num -= 1
                descriptor.length = size
            if size > descriptor.length:
                num = len(descriptor.blocks) - 1
                for i in range(descriptor.length, size):
                    if i == infoStatic.BLOCK_SIZE * num + infoStatic.BLOCK_SIZE:
                        descriptor.blocks.append(['\0' for i in range(infoStatic.BLOCK_SIZE)])
                        num += 1
                    descriptor.blocks[num][i - num * infoStatic.BLOCK_SIZE] = 0
                descriptor.length = size
            print_ok(f'File {name} was successfully truncated!')
            return
    print_error(f'There is no file with name {name}')
