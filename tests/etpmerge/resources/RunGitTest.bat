@echo off
:: MIT License
::
:: Copyright (c) 2023 ANSYS, Inc. All rights reserved.
::
:: Permission is hereby granted, free of charge, to any person obtaining a copy
:: of this software and associated documentation files (the "Software"), to deal
:: in the Software without restriction, including without limitation the rights
:: to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
:: copies of the Software, and to permit persons to whom the Software is
:: furnished to do so, subject to the following conditions:
::
:: The above copyright notice and this permission notice shall be included in all
:: copies or substantial portions of the Software.
::
:: THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
:: IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
:: FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
:: AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
:: LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
:: OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
:: SOFTWARE.

:: create new branches to exercise the merge on each test project
:: --> analyze the differences between project.etp and project.xml in each
::     directory
::
:: - create a branch test/%1
:: - for each sub-directory:
::   - duplicate base.etp to project.etp and project.xml
::   - add the two new files to Git
:: - commit
:: - create a branch test/%1_ex
:: - for each sub-directory
::   - copy remote.etp to project.etp and project.xml
:: - commit
:: - check out test/%1
:: - for each sub-directory
::   - copy local.etp to project.etp and project.xml
:: - commit
:: - merge test/%1_ex to test/1%
:: - compare the files merge.etp and project.etp

SETLOCAL EnableDelayedExpansion

if "%1"=="" (
    echo please provide a base name for the branches to create
    goto :end
)

git checkout -b test/%1
for /D %%v in (*.) do (
    if exist %%v\Base.etp (
        copy %%v\Base.etp %%v\Project.etp
        git add %%v\Project.etp
        copy %%v\Base.etp %%v\Project.xml
        git add %%v\Project.xml
    )
)
git commit -m "initialize the projects"
git checkout -b test/%1_ex
for /D %%v in (*.) do (
    if exist %%v\Remote.etp (
        copy %%v\Remote.etp %%v\Project.etp
        git add %%v\Project.etp
        copy %%v\Remote.etp %%v\Project.xml
        git add %%v\Project.xml
    )
)
git commit -m "remote change"
git checkout test/%1
for /D %%v in (*.) do (
    if exist %%v\Local.etp (
        copy %%v\Local.etp %%v\Project.etp
        git add %%v\Project.etp
        copy %%v\Local.etp %%v\Project.xml
        git add %%v\Project.xml
    )
)
git commit -m "local change"
git merge test/%1_ex
for /D %%v in (*.) do (
    if exist %%v\Merge.etp (
        fc /L /N /T %%v\Merge.etp %%v\Project.etp
    )
)

:end
echo - done.
