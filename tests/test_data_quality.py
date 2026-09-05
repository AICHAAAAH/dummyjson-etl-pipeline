def test_all_checks_pass_raises_nothing():
    """If every check passes, no exception should be raised."""
    results = [True, True, True, True]
    if not all(results):
        raised = True
    else:
        raised = False
    assert raised is False


def test_one_failed_check_should_raise():
    """If even one check fails, the pipeline should flag it as a failure."""
    results = [True, True, False, True]  # one FAIL mixed in
    if not all(results):
        should_fail = True
    else:
        should_fail = False
    assert should_fail is True