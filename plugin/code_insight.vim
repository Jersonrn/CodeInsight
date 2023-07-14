" autocmd WinClosed * call CodeInsightWinClosed(win_getid())
autocmd WinClosed * call CodeInsightWinClosed(+expand('<amatch>'))
