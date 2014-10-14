from fabric.operations import _AttributeString


def get_mock_key_file(tmpdir):
    tmp_file = tmpdir.join("secret.pem")
    tmp_file.write('secret')
    return tmp_file.strpath


def get_mock_ssh_text(text, code):
    result = _AttributeString(text)
    result.return_code = code
    return result
