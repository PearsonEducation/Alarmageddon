from alarmageddon.validations.validation import Validation
import time


class _AttributeString(str):
    """
    Simple string subclass to allow arbitrary attribute access.

    Stolen from fabric1
    """
    @property
    def stdout(self):
        return str(self)


def get_mock_key_file(tmpdir):
    tmp_file = tmpdir.join("secret.pem")
    tmp_file.write('secret')
    return tmp_file.strpath


def get_mock_ssh_text(text, code):
    result = _AttributeString(text)
    result.return_code = code
    return result

class NeverFinish(Validation):
    #don't actually never finish, that would be bad if we don't handle it well
    def perform(self, group_failures):
        time.sleep(60)
