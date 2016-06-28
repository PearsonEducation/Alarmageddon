
def format_node(cluster_name, node):
    """Formats a string representation of a node."""
    return '<{0}[{1}]>'.format(cluster_name, node)


def format_cluster(cluster_name):
    """Formats a string representation of a cluster."""
    return format_node(cluster_name, '*')
