import pytest
import platform
try:
    import setproctitle
except ImportError:
    setproctitle = None

from vcli.main import obfuscate_process_password


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason='Not applicable in windows')
@pytest.mark.skipif(not setproctitle,
                    reason='setproctitle not available')
def test_obfuscate_process_password():
    original_title = setproctitle.getproctitle()

    setproctitle.setproctitle('vcli vertica://dbadmin:pass@localhost/dbname')
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    assert title == 'vcli vertica://dbadmin:xxxx@localhost/dbname'

    setproctitle.setproctitle('vcli -h localhost -U dbadmin -w pass dbname')
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    assert title == 'vcli -h localhost -U dbadmin -w xxxx dbname'

    setproctitle.setproctitle(
        'vcli --host=localhost --user=dbadmin --password=pass dbname')
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    assert title == (
        'vcli --host=localhost --user=dbadmin --password=xxxx dbname')

    setproctitle.setproctitle(original_title)
