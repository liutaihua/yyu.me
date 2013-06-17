--
layout: post
Title: "hosts文件解析域名到多个IP"
Date: 2013-06-16 02:43
comments: true
categories: notes
--

之前一直以为 hosts 不支持把一个名字解析到多个 IP，因此凡是有解析到多个 IP 需求的场景，全部都使用了 DNS，偶然看 host.conf 的 man page，发现并不是这样，有些场景下仍然是可以使用 hosts 的。

使用 hosts 解析时，resolver 顺序读取 hosts 文件，返回第一条匹配记录对应的 IP，这也是我之前对 hosts 的理解，比如对于这样的 hosts 文件:  

1.1.1.1 host1

1.1.1.2 host1


ping host1 会看到 1.1.1.1 这个 IP，但如果在 /etc/host.conf 中设置 multi on，虽然 ping host1 仍然只能看到 1.1.1.1 这个 IP，但 resolver 会返回 hosts 中对应于 host1 条目的所有 IP，以 Python 为例：  

#####>>> socket.gethostbyname_ex('host1')  

('host1', [], ['1.1.1.1', '1.1.1.2'])  

获取到的 IP 列表顺序和 hosts 中定义的顺序一样，且是固定的，这与 Round-robin DNS 的行为仍有区别，但在有些场景下使用 hosts + 推送 + nscd 名字缓存可以获得相对于 DNS 更好的总体性能和稳定性，比如doubanservice 客户端获取服务器列表或许就可以改为使用 hosts 替换 DNS，获得更好的性能，同时也规避了比如 tinydns 对一个名字最多只返回 8 个 IP 地址的问题。