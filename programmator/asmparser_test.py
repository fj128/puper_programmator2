import pytest
from asmparser import parse_asm, Org, Db

def test_org_working():
    assert list(parse_asm(['org 1AH'])) == [Org(26)]
    assert list(parse_asm(['org 09d'])) == [Org(9)]
    assert list(parse_asm(['org 011'])) == [Org(11)]
    assert list(parse_asm(['org 010001b'])) == [Org(17)]
    assert list(parse_asm(['oRg 011Q'])) == [Org(9)]
    assert list(parse_asm(['org 011o'])) == [Org(9)]
    assert list(parse_asm(['org 011b'])) == [Org(3)]


def test_db_working():
    assert list(parse_asm(['db 1AH'])) == [Db([26])]
    assert list(parse_asm(['db 1AH,0,1'])) == [Db([26, 0, 1])]
    assert list(parse_asm([' db  1b , 10b , 11b '])) == [Db([1, 2, 3])]
    assert list(parse_asm([' db 1, 2, '])) == [Db([1, 2])]


def test_errors():
    def expect_error(code, error):
        with pytest.raises(Exception) as exc:
            list(parse_asm(code.split('\n')))
        assert exc.match(error)

    expect_error('asd', 'No arguments for directive')
    expect_error('asd 1', 'Unknown directive')

    expect_error('org', 'No arguments for directive')
    expect_error('org asd', 'Invalid number')
    expect_error('org 0x01', 'Invalid number')
    expect_error('org 02b', 'Invalid number')
    expect_error('org 99q', 'Invalid number')

    expect_error('db', 'No arguments for directive')
    expect_error('db asd', 'Invalid number')
    expect_error('db 1 2', 'Unrecognized token')


if __name__ == "__main__":
    pytest.main([__file__])
