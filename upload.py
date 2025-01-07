import imghdr


def validate_image(stream):
    print(12121212)
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

# defines if files exist
def file_exist(stream):
    print('does file exist?')
    header = str(stream.read(512))
    stream.seek(0)
    if header != "b''":
        return 'Ok'